import time, os, json, fcntl, tempfile, shutil

from pathlib import Path
from .cruds import rfsc_runner
from .config import BASE_DIR, QUEUE_NAME, TOKEN, RATE_LIMIT_QUEUE, RATE_LIMIT_RSFC_ENABLED, RETRYABLE_ERRORS
from .rabbitmq import rabbit_connect
from datetime import datetime
from contextlib import contextmanager
from .repository_state import build_rsfc_repository_paths, promote_staged_rsfc_results
MAX_RETRIES = 7


def timestamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
    


###### Auxiliares
def write_repository_failed_assessment(active_dir: str | Path,response_status: dict) -> Path:
    active_path = Path(active_dir)
    active_path.mkdir(parents=True, exist_ok=True)

    failed_file = active_path / "failed_assessment.json"

    write_json_atomic(
        str(failed_file),
        {"detail": response_status},
    )

    return failed_file

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
def record_rsfc_repository_result(target,repository_url,succeeded):
    with acquire_status_lock(target) as status_file:
        if not os.path.isfile(status_file):
            raise FileNotFoundError(
                f"Status file not initialized: {status_file}"
            )

        with open(status_file, "r", encoding="utf-8") as file:
            status_data = json.load(file)

        expected_repos = int(status_data["expected_repos"])
        processed_repos = min(
            int(status_data["processed_repos"]) + 1,
            expected_repos,
        )
        successful_repos = int(
            status_data.get("successful_repos", 0)
        )
        failed_repos = list(
            status_data.get("failed_repos", [])
        )

        if succeeded:
            successful_repos = min(
                successful_repos + 1,
                expected_repos,
            )
        elif repository_url not in failed_repos:
            failed_repos.append(repository_url)

        status_data["processed_repos"] = processed_repos
        status_data["successful_repos"] = successful_repos
        status_data["failed_repos"] = failed_repos

        if processed_repos < expected_repos:
            status_data["status"] = "processing"
        elif failed_repos:
            status_data["status"] = "failed"
        else:
            status_data["status"] = "completed"

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
def rsfc_indicators_generation(job_id,target,repo_url,base_dir,token):
    
    repository_paths = build_rsfc_repository_paths(base_dir,target,repo_url)
    repository_paths.staging_root.mkdir(parents=True,exist_ok=True)

    succeeded = False
    last_status = {}

    for attempt in range(MAX_RETRIES):
        staging_path = Path(
            tempfile.mkdtemp(prefix=f"{repository_paths.active_dir.name}-",
                            dir=repository_paths.staging_root)
            )

        try:
            response = rfsc_runner(str(staging_path),repo_url,token)
            last_status = response.status

            if last_status["status"] == "success":
                try:
                    promote_staged_rsfc_results(staging_path,repository_paths.active_dir,
                                                )
                except RuntimeError as exc:
                    last_status = {
                        "status": "error",
                        "returncode": -1,
                        "stdout": "",
                        "stderr": str(exc)
                    }
                else:
                    succeeded = True
                    break

            error_text = str(last_status)
            retryable = any(error in error_text for error in RETRYABLE_ERRORS)

            if not retryable:
                break

            retry_number = attempt + 1

            if retry_number >= MAX_RETRIES:
                timestamp(f"[{job_id}] max retries reached")
                break

            timestamp(f"[{job_id}] retry {retry_number}/{MAX_RETRIES} due to network error")
            time.sleep(min(2 ** retry_number * 5, 300))

        finally:
            if staging_path.exists():
                shutil.rmtree(staging_path)

    if not succeeded:
        write_repository_failed_assessment(repository_paths.active_dir, last_status)

    status_data = record_rsfc_repository_result(target, repo_url, succeeded)

    timestamp(f"[RSFC] {target} Progress: {status_data['processed_repos']}/{status_data['expected_repos']} repos processed")

    return succeeded
            
            

# carga del mensaje de la cola y envío a background
def process_message(ch, method, properties, body):
    job_id = "unknown"
    try:
        message = json.loads(body.decode())
        job_id = message["job_id"]
        repo_url = message["repo_url"]
        target = message["target"]

        start = time.time()
        timestamp(f"[{job_id}] Received job")

        if RATE_LIMIT_RSFC_ENABLED:
            wait_for_token(ch)

        succeeded = rsfc_indicators_generation(job_id,target,repo_url,BASE_DIR,TOKEN)

        total_time = time.time() - start

        result = "completed" if succeeded else "failed"

        timestamp(f"[{job_id}] {result} in {total_time:.2f}s")

        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        timestamp(f"[{job_id}] Error processing job: {e}")
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
