import time, os, json, shutil

from .rabbitmq.client import rabbit_connect, publish_job
from .cruds.functions import soca_extract, soca_portal

from .config import QUEUE_NAME, BASE_DIR, RATE_LIMIT_QUEUE, RATE_LIMIT_SOCA_ENABLED
from datetime import datetime



    


###### Auxiliares

def timestamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
    
    
def get_repo_count(target):
    repos_file = os.path.join(BASE_DIR, "outputs", "soca", target, "repos.txt")

    with open(repos_file, "r") as f:
        return len([line for line in f if line.strip()])
    
    

def count_processed(metadata_dir):
    return len([
        f for f in os.listdir(metadata_dir)
        if f.endswith(".json")
    ])


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
def cleanup_repo_dir(metadata_dir, repo_name):
    repo_dir = os.path.join(metadata_dir, repo_name)

    if not os.path.isdir(repo_dir):
        timestamp(f"[CLEANUP] Repo dir not found: {repo_dir}")
        return

    try:
        shutil.rmtree(repo_dir)
        timestamp(f"[CLEANUP] Deleted repo dir: {repo_dir}")
    except Exception as e:
        timestamp(f"[CLEANUP] Error deleting repo dir {repo_dir}: {str(e)}")

# extraccion de metadata
def handle_extract_metadata(target, repo_url):
    
    repo_name = repo_url.rstrip("/").split("/")[-1]
    target_dir = os.path.join(BASE_DIR, "outputs", "soca", target)


    start = time.time()

    # ejecutar extracción
    response = soca_extract(BASE_DIR, target, repo_url)

    # caso error, genera carpeta con fichero status error
    if response.status["status"] == "error":
        timestamp(f"    [{target} - {repo_name}]extract_metadata failed: {response.status}")
        
        metadata_dir = os.path.join(BASE_DIR, "outputs", "soca", target, "metadata")
        os.makedirs(metadata_dir,exist_ok=True)
        
        failed_file = os.path.join(metadata_dir, f"failed_{repo_name}.json")
        with open(failed_file, "w") as f:
            json.dump({"detail": response.status}, f, indent=2)
        
            
    else:
        
        total_time = time.time() - start
        timestamp(f"[{target} - {repo_name}]  Metadata extracted in {total_time:.2f}s ")



    # conteo de repos procesados
    metadata_dir = os.path.join(BASE_DIR, "outputs", "soca", target, "metadata")
    processed = count_processed(metadata_dir)
    
    # eliminacion de repositorio extraido 
    cleanup_repo_dir(metadata_dir, repo_name)
    repo_count = get_repo_count(target)
    
    timestamp(f"[SOCA] {target} Progress: {processed}/{repo_count} repos processed")

    # si todo procesado genera fichero ok
    if processed == repo_count:
        timestamp(f"[{target}] All repos processed")
        
        
        
        
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
            
            handle_extract_metadata(target, repo_url)
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