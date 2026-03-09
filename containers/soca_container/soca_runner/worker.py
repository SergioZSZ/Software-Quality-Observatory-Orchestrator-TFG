import time, os, json, random, pika, uuid, portalocker

from .rabbitmq.client import rabbit_connect, publish_job
from .cruds.functions import soca_extract, soca_portal

from .config import QUEUE_NAME, BASE_DIR, RATE_LIMIT_QUEUE


###### Auxiliares

### lock update
def update_status_file(path, update_fn, target:str | None = None, response:dict | None= None):
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
        json.dump(data, f)
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


    metadata_dir = os.path.join(BASE_DIR, "outputs", "soca", target, "metadata")
    processed = len([f for f in os.listdir(metadata_dir) if f.endswith(".json")])
    # si todos procesados
    if processed == data["repo_count"] and not data.get("portal_launched", False):

        data["portal_launched"] = True
        data["status"] = "completed"
        data["detail"] = response.status

        print("All repos processed. Launching portal generation", flush=True)
        publish_job(target, "portal_generation")






# evitar github
def wait_for_token(channel):

    method, properties, body = channel.basic_get(queue=RATE_LIMIT_QUEUE)

    while method is None:
        time.sleep(1)
        method, properties, body = channel.basic_get(queue=RATE_LIMIT_QUEUE)

    channel.basic_ack(method.delivery_tag)
    
    
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

        print(f"        [{target} - {repo_name}]extract_metadata failed:", response.status, flush=True)
        return

    total_time = time.time() - start
    print(f"        [{target} - {repo_name}] Metadata extracted in {total_time:.2f}s", flush=True)

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

        print("     portal_generation failed:", response.status, flush=True)
        return

    # success
    total_time = time.time() - start
    print(f"        Portal generated in {total_time:.2f}s", flush=True)

    update_status_file(status_file_path,set_completed, response=response)
        
        
        
        
        
### logica externa del worker

def process_message(ch, method, properties, body):
    try:
        
        # cargamos mensaje y el tipo de work
        message = json.loads(body.decode())

        target = message["target"]
        work_type = message["work_type"]

        #wait for token(github ratelimit) 
        wait_for_token(ch)
        
        # division de tipo de trabajo
        if work_type == "extract_metadata":
            repo_url = message["repo_url"]
            repo_name = repo_url.rstrip("/").split("/")[-1]

            print(f"({work_type}) Received job [{target} - {repo_name}]", flush=True)

            status_file_path = os.path.join(BASE_DIR, "outputs", "soca", target, "metadata_status.json")
            
            handle_extract_metadata(target, repo_url, status_file_path)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        elif work_type == "portal_generation":
            
            print(f"({work_type}) Received job [{target}]", flush=True)

            status_file_path = os.path.join(BASE_DIR, "outputs", "soca", target, "portal_status.json")

            handle_portal_generation(target,status_file_path)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        else:
            print(f"Unknown job type: {work_type}", flush=True)



    except Exception as e:
        print("Worker error:", e, flush=True)
        ch.basic_ack(delivery_tag=method.delivery_tag)

        
        
        
        
        
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