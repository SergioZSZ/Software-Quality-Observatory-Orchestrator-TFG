import time, os, json, random, pika, uuid

from .database import SessionLocal, Job
from .cruds import rfsc_runner
from .config import BASE_DIR, QUEUE_NAME, TOKEN, RATE_LIMIT_QUEUE, RATE_LIMIT_RSFC_ENABLED, RETRYABLE_ERRORS
from .rabbitmq import rabbit_connect
from datetime import datetime
from sqlalchemy import func

MAX_RETRIES = 3


def timestamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
    


def wait_for_token(channel):

    # esperamos a que haya token
    while True:
        method, properties, body = channel.basic_get(queue=RATE_LIMIT_QUEUE)

        if method:
            channel.basic_ack(method.delivery_tag)
            return

        time.sleep(0.5)

            
            
#llamada a rsfc_runner y cambios de estado de la bbdd
def rsfc_indicators_generation(job_id, repo_url, base_dir, token, retries):
    # creamos sesion db
    db = SessionLocal()
    try:
        #cogemos el job por su id si existe y cambiamos estado a running
        job = db.get(Job, job_id)
        if not job:
            timestamp(f"\n\n\n (RSFC)[{job_id}] ERROR: job does not exist \n\n\n")
            return
        
        job.status = "running"
        db.commit()
        
        while retries < MAX_RETRIES:
            # ejecutamos rsfc_runner por cada worker
            response = rfsc_runner(base_dir, str(repo_url), token)
            error_text = str(response.status)
            retryable = any(err in error_text for err in RETRYABLE_ERRORS)
            #si no error rompemos retries o si es error no 
            if response.status["status"] == "success" or not retryable :
                break

            # si es de los errores marcados para retry (conexion o timeout) lo intentamos 3 veces como max
            if retryable:
                retries += 1
                if retries <= MAX_RETRIES:
                    timestamp(f"[{job_id}] retry {retries}/{MAX_RETRIES} due to network error")
                    time.sleep(10*retries)
                    continue
                else:
                    timestamp(f"[{job_id}] max retries reached")
                    break
            else:
                break
            
        # si es error distinto a los volver a intentar
        if response.status["status"] == "error":
            

            timestamp(f"\n\n\n*******************************************************************************************\n{response.status}*******************************************************************************************\n\n\n")

            job.status = "error"
            job.detail = {"error": response.status}
            
            
            db.commit()
            return  

        #buscamos indicadores generados 
        indicators = os.path.join(response.personal_dir, "rsfc_output","rsfc_assessment.json")

        if not os.path.exists(indicators):
            job.status = "error"
            job.detail = {"error": response.status}
            
            timestamp(response.status)
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
        
        completed = db.query(func.count(Job.id)).filter(Job.status == "success").scalar()
        total_jobs = db.query(func.count(Job.id)).scalar()
        timestamp(f"[RSFC] Progress: {completed}/{total_jobs} repos processed")
    # excepciones posibles
    except Exception as e:
        
        job = db.get(Job, job_id)

        if job:
            job.status = "error"
            job.detail = {"error": str(e)}
            db.commit()
            
            timestamp(f"\n\n\nJob {job_id} failed: {str(e)}\n\n\n")
            
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
        timestamp(f"Received job {job_id}")

        # procesamos mensaje pero nates  limit
        if RATE_LIMIT_RSFC_ENABLED:
            wait_for_token(ch)
            
        rsfc_indicators_generation(job_id, repo_url, BASE_DIR, TOKEN, 0)

        total_time = time.time() - start
        
        timestamp(f"Job {job_id} completed in: {total_time:.2f}s")
        
        # evitar saturar github api 
        
        #confirmacion de mensaje pocesado para eliminarlo de la cola
        ch.basic_ack(delivery_tag=method.delivery_tag)


        
    except Exception as e:
        # si falla lo metemos en la cola (faltaría revisar si el error es para meter en cola)
        timestamp(f"\n\n\n[{job_id}] failed: {str(e)}\n\n\n")
        ch.basic_ack(delivery_tag=method.delivery_tag)






# establecimiento de conexion con cola y escucha
def worker():
    timestamp("** WORKER STARTED **")
    
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
    
    timestamp("Waiting for jobs...")

    channel.start_consuming()
            
            
            
            
            
if __name__ == "__main__":
    worker()