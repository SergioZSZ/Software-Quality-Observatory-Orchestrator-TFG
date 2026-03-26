import time, os, json

from .cruds import rfsc_runner
from .config import BASE_DIR, QUEUE_NAME, TOKEN, RATE_LIMIT_QUEUE, RATE_LIMIT_RSFC_ENABLED, RETRYABLE_ERRORS
from .rabbitmq import rabbit_connect
from datetime import datetime

MAX_RETRIES = 7


def timestamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
    


def count_jsons(base_path):
    count = 0
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".json"):
                count += 1
    return count




def wait_for_token(channel):

    # esperamos a que haya token
    while True:
        method, properties, body = channel.basic_get(queue=RATE_LIMIT_QUEUE)

        if method:
            channel.basic_ack(method.delivery_tag)
            return

        time.sleep(0.5)

            
            
#llamada a rsfc_runner y cambios de estado de la bbdd
def rsfc_indicators_generation(job_id,target, repo_url,repos_count, base_dir, token, retries):
    # creamos sesion db
        
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
                if retries < MAX_RETRIES:
                    timestamp(f"[{job_id}] retry {retries}/{MAX_RETRIES} due to network error")
                    time.sleep(2 ** retries * 30)
                    continue
                else:
                    timestamp(f"[{job_id}] max retries reached")
                    break
            else:
                break
            
        # si es error distinto a los volver a intentar o demasiados retries, generamos failed file
        if response.status["status"] == "error":
            

            timestamp(f"\n\n\n\n\n\n*******************************************************************************************\n{json.dumps(response.status, indent=2)}*******************************************************************************************\n\n\n\n\n\n")
            repo_name = repo_url.rstrip("/").split("/")[-1]
            failed_repo_dir = os.path.join(BASE_DIR,"rsfc",target,repo_name)
            os.makedirs(failed_repo_dir,exist_ok=True)
            
            failed_job = {"detail": response.status}
            failed_job_file = os.path.join(failed_repo_dir,"failed_assessment.json")
            
            with open(failed_job_file,"w") as f:
                json.dump(failed_job,f, indent=2)

            if retryable:
                return True
            return False

        #b uscamos todos los .json del directorio target para logs
        rsfc_target_dir = os.path.join(BASE_DIR,"outputs", "rsfc", target)
        completed = count_jsons(rsfc_target_dir)

        timestamp(f"[RSFC] {target} Progress: {completed}/{repos_count} repos processed")
        
        
        # caso completado empieza dashverse
        if completed == repos_count:
            timestamp(f"[{target}] All repos processed")
        
        return False
            
            

# carga del mensaje de la cola y envío a background
def process_message(ch, method, properties, body):
    try:
        
        # cargamos mensaje y cambiamos job de string a uuid
        message = json.loads(body.decode())
        job_id = message["job_id"]
        repo_url = message["repo_url"]
        target = message["target"]
        repos_count = message["repos_count"]

        start = time.time()
        timestamp(f"[{job_id}] Received job")

        # procesamos mensaje pero nates  limit
        if RATE_LIMIT_RSFC_ENABLED:
            wait_for_token(ch)
            
        requeue = rsfc_indicators_generation(job_id, target, repo_url,repos_count, BASE_DIR, TOKEN, 0)

        total_time = time.time() - start
        
        timestamp(f"[{job_id}] completed in: {total_time:.2f}s")
        
        # evitar saturar github api 
        
        #confirmacion de mensaje pocesado para eliminarlo de la cola
        if requeue:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        


        
    except Exception as e:
        # si falla lo metemos en la cola (faltaría revisar si el error es para meter en cola)
        timestamp(f"\n\n\n[ {job_id}] failed: {str(e)}\n\n\n")
        ch.basic_ack(delivery_tag=method.delivery_tag)






# establecimiento de conexion con cola y escucha
def worker():
    timestamp("** WORKER STARTED **")
    
    # definicion de credenciales, la conexion, credenciales y apertura de canal
    connection = rabbit_connect()
    channel = connection.channel()


    # worker recibe 1 trabajo y recibe el siguiente al terminar
    channel.basic_qos(prefetch_count=1)
    
    # escuchar cola queue procesando por callback dado
    channel.basic_consume( queue=QUEUE_NAME, on_message_callback=process_message)
    
    timestamp("Waiting for jobs...")

    channel.start_consuming()
            
            
            
            
            
if __name__ == "__main__":
    worker()