import time, os, json, random, pika, uuid

from .database import SessionLocal, Job
from .cruds import rfsc_runner
from .config import BASE_DIR, QUEUE_NAME, TOKEN, RATE_LIMIT_QUEUE, RATE_LIMIT_RSFC_ENABLED
from .rabbitmq import rabbit_connect

# 
def wait_for_token(channel):

    method, properties, body = channel.basic_get(queue=RATE_LIMIT_QUEUE)

    while method is None:
        time.sleep(0.5)
        method, properties, body = channel.basic_get(queue=RATE_LIMIT_QUEUE)

    channel.basic_ack(method.delivery_tag)

            
            
#llamada a rsfc_runner y cambios de estado de la bbdd
def run_in_background(job_id, repo_url, base_dir, token):
    # creamos sesion db
    db = SessionLocal()
    try:
        #cogemos el job por su id si existe y cambiamos estado a running
        job = db.get(Job, job_id)
        if not job:
            return
        
        job.status = "running"
        db.commit()
        
        # ejecutamos rsfc_runner por cada worker
        response = rfsc_runner(base_dir, str(repo_url), token)

        # si error devolvemos logs
        if response.status["status"] == "error":
            
            print("*******************************************************************************************\n",response.status,"*******************************************************************************************\n")

            # si timeout de rsfc intentarlo una vez mas
            if "ReadTimeout" in response.status["stderr"]:
                if job.retries < 1:
                    job.retries += 1
                    db.commit()
                    time.sleep(30)
                    return run_in_background(job_id, repo_url, base_dir, token) 
        
            
            job.status = "error"
            job.detail = {"error": response.status}
            
            print(response.status, flush=True)
            
            db.commit()
            return

        #buscamos indicadores generados 
        indicators = os.path.join(response.personal_dir, "rsfc_output","rsfc_assessment.json")

        if not os.path.exists(indicators):
            job.status = "error"
            job.detail = {"error": response.status}
            
            print(response.status, flush=True)
            db.commit()
            return
        
        # cargamos indicadores
        with open(indicators) as f:
            data = json.load(f)

        # guardamos job bien ejecutado devolviendo los indicadores
        job.status = "success"
        job.detail = data
        job.result_path = indicators
        db.commit()
                
    # excepciones posibles
    except Exception as e:
        
        print(f"error id {job_id}: {str(e)}")
        job = db.get(Job, job_id)

        if job:
            job.status = "error"
            job.detail = {"error": str(e)}
            db.commit()
            db.refresh(job)
            db.close()
            
            print(f"Job {job_id} failed: ", str(e))
            
    finally:
        db.close()




# carga del mensaje de la cola y envío a background
def process_message(ch, method, properties, body):
    try:
        
        # cargamos mensaje y cambiamos job de string a uuid
        message = json.loads(body.decode())
        job_id = uuid.UUID(message["job_id"])
        repo_url = message["repo_url"]

        start = time.time()
        print(f"Received job {job_id}", flush=True)

        # procesamos mensaje si limit
        if RATE_LIMIT_RSFC_ENABLED:
            wait_for_token(ch)
            
        run_in_background(job_id, repo_url, BASE_DIR, TOKEN)

        total_time = time.time() - start
        print(f"Job {job_id} completed in: {total_time:.2f}s", flush=True)
        
        # evitar saturar github api 
        
        #confirmacion de mensaje pocesado para eliminarlo de la cola
        ch.basic_ack(delivery_tag=method.delivery_tag)


        
    except Exception as e:
        # si falla lo metemos en la cola (faltaría revisar si el error es para meter en cola)
        print(f"[{job_id}] failed, requeueing:", e)
        ch.basic_ack(delivery_tag=method.delivery_tag)






# establecimiento de conexion con cola y escucha
def worker():
    print("** WORKER STARTED **", flush=True)
    
    # definicion de credenciales, la conexion, credenciales y apertura de canal
    connection = rabbit_connect()
    channel = connection.channel()
    
    # verificación de la cola
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.queue_declare(queue=RATE_LIMIT_QUEUE, durable=True, arguments={"x-max-length": 1})

    # worker recibe 1 trabajo y recibe el siguiente al terminar
    channel.basic_qos(prefetch_count=1)
    
    # escuchar cola queue procesando por callback dado
    channel.basic_consume( queue=QUEUE_NAME, on_message_callback=process_message)
    
    print("Waiting for jobs...", flush=True)

    channel.start_consuming()
            
            
            
            
            
if __name__ == "__main__":
    worker()