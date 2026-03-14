import time, os, json, portalocker

from .rabbitmq.client import rabbit_connect, publish_job, publish_event, publish_repo_done
from .cruds.functions import soca_extract, soca_portal

from .config import QUEUE_NAME, BASE_DIR, RATE_LIMIT_QUEUE, RATE_LIMIT_SOCA_ENABLED
from datetime import datetime


def timestamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
    


###### Auxiliares

### lock update
def update_status_file(path, update_fn, target:str| None = None, response:dict | None= None):
    # apertura y lockeo del archivo json para que otros workers no sobrescriban
    with portalocker.Lock(path, 'r+', timeout=10) as f:
        # lectura y actualización a usar
        data = json.load(f)
        
        # caso set running
        if not target and not response:
            update_fn(data)
    
        #caso intento generar portal
        elif target and response:
            update_fn(data,target,response)
        
        # caso set error y completed
        else:
            update_fn(data, response)

        # volver al inicio del archivo y truncarlo para no dejar residuos al final y update json
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)
        f.flush() # mandar los datos directamente (no guardar en buffer)

## funciones para lock update
# set locks
def set_running(data):
    if data["status"] == "queued":
        data["status"] = "running"

def set_error(data, response):
    data["status"] = "error"
    data["detail"] = response.status
    
def set_completed(data,response):
    data["status"] = "completed"
    data["detail"] = response.status

        
# lanzamiento portal lock
def launch_portal(data,target,response):

    data["repos_processed"] += 1 
    
    timestamp(f"[{target}] Progress: {data['repos_processed']}/{data['repo_count']}")
    
    metadata_dir = os.path.join(BASE_DIR, "outputs", "soca", target, "metadata")
    
    # si todos procesados
    if data["repos_processed"] == data["repo_count"]:
        timestamp(f"All repos processed. Communicating with RSFC")
        # evento para empezar rsfc
        
        publish_event(target)
        
        if not data.get("portal_launched", False):
            data["portal_launched"] = True
            data["status"] = "completed"
            data["detail"] = response.status

            timestamp(f"Launching portal generation")
            publish_job(target, "portal_generation")






# evitar github si activado rate limit
def wait_for_token(channel):

    # esperamos a que haya token
    while True:
        method, properties, body = channel.basic_get(queue=RATE_LIMIT_QUEUE)

        if method:
            channel.basic_ack(method.delivery_tag)
            return

        time.sleep(0.5)

    
    
### logica interna del worker

# extraccion de metadata
def handle_extract_metadata(target, repo_url, status_file_path):
    
    repo_name = repo_url.rstrip("/").split("/")[-1]
    

    start = time.time()

    # actualizar estado a running
    update_status_file(status_file_path, set_running)

    # ejecutar extracción
    response = soca_extract(BASE_DIR, target, repo_url)

    # caso error
    if response.status["status"] == "error":
        update_status_file(status_file_path, set_error, response = response)

        timestamp(f"    [{target} - {repo_name}]extract_metadata failed: {response.status}")
        return

    total_time = time.time() - start
    timestamp(f"[{target} - {repo_name}]  Metadata extracted in {total_time:.2f}s ")

    # comprobar si lanzar portal y lanzarlo 
    update_status_file(status_file_path, launch_portal, target=target, response=response)





# generacion de portal
def handle_portal_generation(target,status_file_path):


    start = time.time()

    # actualizar estado a running
    update_status_file(status_file_path, set_running)

    # generacion del portal
    response = soca_portal(BASE_DIR, target)

    # errores 
    if response.status["status"] == "error":
        update_status_file(status_file_path,set_error, response=response)

        timestamp(f"    portal_generation failed: {response.status}")
        return

    # success
    total_time = time.time() - start
    timestamp(f"    Portal generated")

    update_status_file(status_file_path,set_completed, response=response)
        
        
        
        
        
### logica externa del worker

def process_message(ch, method, properties, body):
    try:
        
        # cargamos mensaje y el tipo de work
        message = json.loads(body.decode())

        target = message["target"]
        work_type = message["work_type"]

        #wait for token(github ratelimit si activado)
        if RATE_LIMIT_SOCA_ENABLED:
            wait_for_token(ch)
        
        # division de tipo de trabajo
        if work_type == "extract_metadata":
            repo_url = message["repo_url"]
            repo_name = repo_url.rstrip("/").split("/")[-1]

            timestamp(f"({work_type}) Received job [{target} - {repo_name}]")

            status_file_path = os.path.join(BASE_DIR, "outputs", "soca", target, "metadata_status.json")
            
            handle_extract_metadata(target, repo_url, status_file_path)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        elif work_type == "portal_generation":
            
            timestamp(f"({work_type}) Received job [{target}]")

            status_file_path = os.path.join(BASE_DIR, "outputs", "soca", target, "portal_status.json")

            handle_portal_generation(target,status_file_path)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        else:
            timestamp(f"Unknown job type: {work_type}")



    except Exception as e:
        timestamp(f"\n\nWorker error: {str(e)}\n\n")
        ch.basic_ack(delivery_tag=method.delivery_tag)

        
        
        
        
        
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