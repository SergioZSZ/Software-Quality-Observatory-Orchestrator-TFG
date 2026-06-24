import time, os, json, shutil, fcntl, tempfile

from .rabbitmq.client import rabbit_connect, publish_job
from .cruds.functions import soca_extract, soca_portal

from .config import QUEUE_NAME, BASE_DIR, RATE_LIMIT_QUEUE, RATE_LIMIT_SOCA_ENABLED
from datetime import datetime
from contextlib import contextmanager


STATUS_FILENAME = "status.json"
STATUS_LOCK_FILENAME = "status.lock"




###### Auxiliares

def timestamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# obtener rutas del status y de su fichero de bloqueo
def get_status_paths(target):
    target_dir = os.path.join(BASE_DIR, "outputs", "soca", target)
    status_file = os.path.join(target_dir, STATUS_FILENAME)
    lock_file = os.path.join(target_dir, STATUS_LOCK_FILENAME)

    return target_dir, status_file, lock_file


# bloquear acceso al status para que solo un worker pueda modificarlo
@contextmanager
def acquire_status_lock(target):
    target_dir, status_file, lock_file = get_status_paths(target)
    os.makedirs(target_dir, exist_ok=True)

    # el lock se mantiene en un fichero independiente porque status.json se reemplaza
    with open(lock_file, "a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)

        try:
            yield status_file
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


# escribir status de forma atomica para evitar jsons parciales
def write_status_atomic(status_file, status_data):
    status_dir = os.path.dirname(status_file)

    file_descriptor, temporary_file = tempfile.mkstemp(
        prefix=".status_",
        suffix=".tmp",
        dir=status_dir,
    )

    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            json.dump(status_data, file, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_file, status_file)

    except Exception:
        if os.path.exists(temporary_file):
            os.remove(temporary_file)

        raise


# incrementar repos procesados manteniendo exclusion mutua entre workers
def increment_processed_repos(target):
    with acquire_status_lock(target) as status_file:

        if not os.path.isfile(status_file):
            raise FileNotFoundError(
                f"Status file not initialized: {status_file}"
            )

        with open(status_file, "r", encoding="utf-8") as file:
            status_data = json.load(file)

        expected_repos = int(status_data["expected_repos"])
        processed_repos = int(status_data["processed_repos"])

        # incrementar sin permitir superar el numero esperado
        processed_repos = min(processed_repos + 1, expected_repos)

        status_data["processed_repos"] = processed_repos

        # marcar completed cuando todos los repos han terminado
        if processed_repos >= expected_repos:
            status_data["status"] = "completed"
        else:
            status_data["status"] = "processing"

        write_status_atomic(status_file, status_data)

        return status_data.copy()


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
    metadata_dir = os.path.join(target_dir, "metadata")

    os.makedirs(metadata_dir, exist_ok=True)

    start = time.time()

    try:
        # ejecutar extracción
        response = soca_extract(BASE_DIR, target, repo_url)

        # caso error, genera carpeta con fichero status error
        if response.status["status"] == "error":
            timestamp(f"    [{target} - {repo_name}]extract_metadata failed: {response.status}")

            failed_file = os.path.join(metadata_dir, f"failed_{repo_name}.json")
            with open(failed_file, "w", encoding="utf-8") as f:
                json.dump({"detail": response.status}, f, indent=2)

        else:

            total_time = time.time() - start
            timestamp(f"[{target} - {repo_name}]  Metadata extracted in {total_time:.2f}s ")

    # caso excepcion inesperada, genera tambien fichero status error
    except Exception as e:
        timestamp(f"    [{target} - {repo_name}]extract_metadata failed: {str(e)}")

        failed_file = os.path.join(metadata_dir, f"failed_{repo_name}.json")
        with open(failed_file, "w", encoding="utf-8") as f:
            json.dump({"detail": str(e)}, f, indent=2)

    # eliminacion de repositorio extraido
    cleanup_repo_dir(metadata_dir, repo_name)

    # actualizar conteo de repos procesados con bloqueo exclusivo
    status_data = increment_processed_repos(target)

    timestamp(
        f"[SOCA] {target} Progress: "
        f"{status_data['processed_repos']}/{status_data['expected_repos']} "
        f"repos processed"
    )

    # si todo procesado cambia status a completed
    if status_data["status"] == "completed":
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
            ch.basic_ack(delivery_tag=method.delivery_tag)



    except Exception as e:
        timestamp(f"\n\nWorker error: {str(e)}\n\n")

        # si falla la actualizacion del status no perder el trabajo
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True,
        )






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
