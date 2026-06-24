import time, os, json, fcntl, tempfile

from .cruds import rfsc_runner
from .config import BASE_DIR, QUEUE_NAME, TOKEN, RATE_LIMIT_QUEUE, RATE_LIMIT_RSFC_ENABLED, RETRYABLE_ERRORS
from .rabbitmq import rabbit_connect
from datetime import datetime
from contextlib import contextmanager

MAX_RETRIES = 7


def timestamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
    


###### Auxiliares

# rutas del fichero de estado y del fichero lock compartido entre workers
def get_status_paths(target):
    target_dir = os.path.join(BASE_DIR, "outputs", "rsfc", target)

    os.makedirs(target_dir, exist_ok=True)

    status_file = os.path.join(target_dir, "status.json")
    lock_file = os.path.join(target_dir, "status.lock")

    return status_file, lock_file


# bloqueo exclusivo para que solo un worker acceda al status a la vez
@contextmanager
def acquire_status_lock(target):
    status_file, lock_file = get_status_paths(target)

    # el lock debe estar en el volumen outputs compartido por todos los workers
    with open(lock_file, "a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)

        try:
            yield status_file
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


# escritura atomica para evitar que otro worker lea un json incompleto
def write_json_atomic(file_path, data):
    directory = os.path.dirname(file_path)

    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix=".status_",
        suffix=".tmp",
        dir=directory,
    )

    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as temporary_file:
            json.dump(data, temporary_file, indent=2)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, file_path)

    except Exception:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)

        raise


# incremento protegido del numero de repositorios procesados
def increment_processed_repos(target):

    # se bloquea el ciclo completo leer, incrementar y escribir
    with acquire_status_lock(target) as status_file:
        if not os.path.isfile(status_file):
            raise FileNotFoundError(
                f"Status file not initialized: {status_file}"
            )

        with open(status_file, "r", encoding="utf-8") as file:
            status_data = json.load(file)

        expected_repos = int(status_data["expected_repos"])
        processed_repos = int(status_data["processed_repos"])

        processed_repos += 1

        # evitamos superar el numero de repositorios esperados
        processed_repos = min(processed_repos, expected_repos)

        status_data["processed_repos"] = processed_repos

        if processed_repos >= expected_repos:
            status_data["status"] = "completed"
        else:
            status_data["status"] = "processing"

        write_json_atomic(status_file, status_data)

        return status_data.copy()



def wait_for_token(channel):

    # esperamos a que haya token
    while True:
        method, properties, body = channel.basic_get(queue=RATE_LIMIT_QUEUE)

        if method:
            channel.basic_ack(method.delivery_tag)
            return

        time.sleep(0.5)

            
            
#llamada a rsfc_runner y cambios de estado de la bbdd
def rsfc_indicators_generation(job_id, target, repo_url, repos_count, base_dir, token, retries):
    # creamos sesion db
        
        while retries < MAX_RETRIES:
            # ejecutamos rsfc_runner por cada worker
            response = rfsc_runner(base_dir, target, str(repo_url), token)
            error_text = str(response.status)
            retryable = any(err in error_text for err in RETRYABLE_ERRORS)

            #si no error rompemos retries o si es error no reintentable
            if response.status["status"] == "success" or not retryable:
                break

            # si es de los errores marcados para retry (conexion o timeout) lo intentamos hasta MAX_RETRIES
            if retryable:
                retries += 1
                if retries < MAX_RETRIES:
                    timestamp(f"[{job_id}] retry {retries}/{MAX_RETRIES} due to network error")
                    time.sleep(min(2 ** retries * 5, 300))
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
            failed_repo_dir = os.path.join(BASE_DIR, "outputs", "rsfc", target, repo_name)
            os.makedirs(failed_repo_dir, exist_ok=True)
            
            failed_job = {"detail": response.status}
            failed_job_file = os.path.join(failed_repo_dir, "failed_assessment.json")
            
            with open(failed_job_file, "w", encoding="utf-8") as f:
                json.dump(failed_job, f, indent=2)

        # incremento del json de estado tanto para exito como para fallo definitivo
        status_data = increment_processed_repos(target)

        timestamp(
            f"[RSFC] {target} Progress: "
            f"{status_data['processed_repos']}/"
            f"{status_data['expected_repos']} repos processed"
        )
        
        
        # caso completado empieza dashverse
        if status_data["status"] == "completed":
            timestamp(f"[{target}] All repos processed")
        
        # los reintentos ya se realizan dentro de esta funcion
        return False
            
            

# carga del mensaje de la cola y envío a background
def process_message(ch, method, properties, body):
    job_id = "unknown"

    try:
        
        # cargamos mensaje y cambiamos job de string a uuid
        message = json.loads(body.decode())
        job_id = message["job_id"]
        repo_url = message["repo_url"]
        target = message["target"]
        repos_count = message["repos_count"]

        start = time.time()
        timestamp(f"[{job_id}] Received job")

        # procesamos mensaje pero antes limit
        if RATE_LIMIT_RSFC_ENABLED == True:
            wait_for_token(ch)
            
        requeue = rsfc_indicators_generation(job_id, target, repo_url, repos_count, BASE_DIR, TOKEN, 0)

        total_time = time.time() - start
        
        timestamp(f"[{job_id}] completed in: {total_time:.2f}s")
        
        # evitar saturar github api 
        
        #confirmacion de mensaje pocesado para eliminarlo de la cola
        if requeue:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        


        
    except Exception as e:
        # si falla antes de actualizar el status lo volvemos a meter en la cola
        timestamp(f"\n\n\n[{job_id}] failed: {str(e)}\n\n\n")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)






# establecimiento de conexion con cola y escucha
def worker():
    timestamp("** WORKER STARTED **")
    
    # definicion de credenciales, la conexion, credenciales y apertura de canal
    connection = rabbit_connect()
    channel = connection.channel()


    # worker recibe 1 trabajo y recibe el siguiente al terminar
    channel.basic_qos(prefetch_count=1)
    
    # escuchar cola queue procesando por callback dado
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message)
    
    timestamp("Waiting for jobs...")

    channel.start_consuming()
            
            
            
            
            
if __name__ == "__main__":
    worker()
