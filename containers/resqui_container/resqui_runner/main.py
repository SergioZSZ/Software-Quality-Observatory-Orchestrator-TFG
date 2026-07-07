from contextlib import contextmanager
import fcntl
import tempfile

from .rabbitmq.client import publish_job
import json,os
from .config import BASE_DIR, INPUT
from .repository_state import build_resqui_repository_paths, parse_github_repository_url, remove_repository_old_results

## Auxiliares
    # rutas del fichero de estado y del fichero lock compartido entre workers
def get_status_paths(target):
    target_dir = os.path.join(BASE_DIR, "outputs", "resqui", target)

    os.makedirs(target_dir, exist_ok=True)

    status_file = os.path.join(target_dir, "status.json")
    lock_file = os.path.join(target_dir, "status.lock")

    return status_file, lock_file


# bloqueo exclusivo para que solo un proceso acceda al status a la vez
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


# escritura atomica para evitar que otro proceso lea un json incompleto
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


# inicializacion del estado antes de publicar los trabajos
def initialize_status(target, expected_repos):
    status_data = {
        "status": "completed" if expected_repos == 0 else "processing",
        "expected_repos": expected_repos,
        "processed_repos": 0,
        "successful_repos": 0,
        "failed_repos": []
    }
    # bloqueo durante toda la escritura inicial del fichero
    with acquire_status_lock(target) as status_file:
        write_json_atomic(status_file, status_data)

    print(f"**\RESQUI status initialized for '{target}': 0/{expected_repos} repositories\n")

def main(input: dict):
    
    repos = input.get("repos_url", [])
    repos_removed = input.get("repos_removed", [])
    repos_count = len(repos)
    target = input.get("target")

    if not target:
        raise RuntimeError("Target name is required")
    
    target_dir = os.path.join(BASE_DIR, "outputs", "resqui",target)

    os.makedirs(target_dir, exist_ok=True)

    # eliminacion de repos eliminados
    for repo_url in repos_removed:
        repository_paths = build_resqui_repository_paths(BASE_DIR,target,repo_url,)
        removed = remove_repository_old_results(repository_paths)
        
        print(f"Removed RESQUI results for {repo_url}: {removed}",flush=True)

    # inicializacion del json de estado antes de enviar trabajos a los workers
    initialize_status(target, repos_count)

    # envío de repositorios a los workers (jobs)
    for repo_url in repos:
        repository = parse_github_repository_url(repo_url)
        job_id = f"{target}_{repository.file_key}"

        publish_job(job_id, repository.url, target, repos_count)


    
        
        

    






if __name__ == "__main__":
    input = json.loads(INPUT)
    main(input)
    