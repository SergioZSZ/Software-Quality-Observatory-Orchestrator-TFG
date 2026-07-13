import time, os, json, fcntl, tempfile

from .rabbitmq.client import rabbit_connect, publish_job
from .cruds.functions import soca_extract, soca_portal

from .config import (
    QUEUE_NAME,
    BASE_DIR,
    RATE_LIMIT_QUEUE,
    RATE_LIMIT_SOCA_ENABLED,
    RATE_LIMIT_WAIT_SECONDS,
)
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from .repository_state import parse_github_repository_url
from .safe_logging import sanitize_data, sanitize_text

STATUS_FILENAME = "status.json"
STATUS_LOCK_FILENAME = "status.lock"




###### Auxiliares

def timestamp(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {sanitize_text(msg)}", flush=True)


def summarize_command_output(status: dict, max_chars: int = 1200) -> str:
    parts = []
    for field in ("stderr", "stdout"):
        value = sanitize_text(status.get(field) or "")
        if not isinstance(value, str):
            value = sanitize_text(value)

        value = value.strip()
        if value:
            parts.append(f"{field.upper()}:\n{value[-max_chars:]}")

    if not parts:
        parts.append(f"STATUS: {sanitize_data(status)}")

    return "\n".join(parts)


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


# Registra el resultado de un repositorio bajo bloqueo exclusivo.
def record_repository_result(
    target,
    repository_url,
    succeeded,
):
    with acquire_status_lock(target) as status_file:
        if not os.path.isfile(status_file):
            raise FileNotFoundError(
                f"Status file not initialized: {status_file}"
            )

        with open(status_file, "r", encoding="utf-8") as file:
            status_data = json.load(file)

        expected_repos = int(
            status_data["expected_repos"]
        )
        processed_repos = int(
            status_data["processed_repos"]
        )
        successful_repos = int(
            status_data.get("successful_repos", 0)
        )
        failed_repos = list(
            status_data.get("failed_repos", [])
        )

        processed_repos = min(
            processed_repos + 1,
            expected_repos,
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

        # Esperar a todos los workers antes de fijar el estado terminal.
        if processed_repos < expected_repos:
            status_data["status"] = "processing"
        else:
            status_data["status"] = "completed"

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

        time.sleep(RATE_LIMIT_WAIT_SECONDS)




### logica interna del worker

# Localiza el único JSON generado para un repositorio en staging.
def find_staged_metadata(
    staging_dir: str,
    repository_key: str,
) -> Path:
    candidates = list(
        Path(staging_dir).glob(
            f"{repository_key}_*.json"
        )
    )

    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected one metadata JSON for "
            f"{repository_key}, found {len(candidates)}"
        )

    return candidates[0]


# Promueve el resultado nuevo y elimina las versiones antiguas
def promote_repository_metadata(
    staged_metadata: Path,
    metadata_dir: str,
    repository_key: str,
) -> Path:
    destination = (
        Path(metadata_dir) / staged_metadata.name
    )

    # Promover primero garantiza que nunca eliminamos el resultado activo
    # antes de disponer de uno nuevo válido
    os.replace(staged_metadata, destination)

    for previous_metadata in Path(metadata_dir).glob(
        f"{repository_key}_*.json"
    ):
        if previous_metadata != destination:
            previous_metadata.unlink()

    # Un resultado correcto elimina el error anterior del repositorio.
    failed_file = (
        Path(metadata_dir)
        / f"failed_{repository_key}.json"
    )
    failed_file.unlink(missing_ok=True)

    return destination


# Extrae y reemplaza los metadatos de un repositorio de forma segura.
def handle_extract_metadata(target, repo_url):
    repository = parse_github_repository_url(repo_url)
    repository_key = repository.file_key

    target_dir = Path(BASE_DIR) / "outputs" / "soca" / target
    metadata_dir = target_dir / "metadata"
    staging_root = target_dir / ".staging"

    metadata_dir.mkdir(parents=True, exist_ok=True)
    staging_root.mkdir(parents=True, exist_ok=True)

    start = time.time()
    extraction_succeeded = False

    try:
        # Cada job utiliza un temporal independiente. Al salir del bloque,
        # también desaparece el clon temporal creado por SOCA.
        with tempfile.TemporaryDirectory(
            prefix=f"{repository_key}_",
            dir=staging_root,
        ) as staging_dir:
            response = soca_extract(
                staging_dir,
                repository.url,
            )

            if response.status["status"] == "error":
                timestamp(
                    f"[{target} - {repository_key}] "
                    f"SOCA extraction failed:\n"
                    f"{summarize_command_output(response.status)}"
                )
                raise RuntimeError(
                    json.dumps(
                        {
                            "message": "SOCA extraction failed",
                            "detail": sanitize_data(response.status),
                            "error_summary": summarize_command_output(
                                response.status
                            ),
                        },
                        ensure_ascii=False,
                    )
                )

            # SOCA puede terminar con código cero sin generar ningún JSON.
            staged_metadata = find_staged_metadata(
                staging_dir,
                repository_key,
            )

            active_metadata = promote_repository_metadata(
                staged_metadata=staged_metadata,
                metadata_dir=str(metadata_dir),
                repository_key=repository_key,
            )

        extraction_succeeded = True
        total_time = time.time() - start

        timestamp(
            f"[{target} - {repository_key}] Metadata extracted "
            f"in {total_time:.2f}s: {active_metadata.name}"
        )

    except Exception as exc:
        # El resultado activo anterior no se elimina si la extracción falla.
        timestamp(
            f"[{target} - {repository_key}] "
            f"extract_metadata failed: {exc}"
        )

        error_detail = {
            "message": "SOCA extract_metadata failed",
            "error": sanitize_text(exc),
        }

        try:
            parsed_error = json.loads(str(exc))
            if isinstance(parsed_error, dict):
                error_detail.update(sanitize_data(parsed_error))
        except json.JSONDecodeError:
            pass

        failed_file = (
            metadata_dir
            / f"failed_{repository_key}.json"
        )

        with failed_file.open("w", encoding="utf-8") as file:
            json.dump(
                {"detail": sanitize_data(error_detail)},
                file,
                indent=2,
            )
            file.write("\n")

    # Por ahora se mantiene el contador actual. En el siguiente paso
    # diferenciaremos entre repositorios correctos y fallidos.
    status_data =record_repository_result(
    target=target,
    repository_url=repository.url,
    succeeded=extraction_succeeded,
)

    timestamp(
        f"[SOCA] {target} Progress: "
        f"{status_data['processed_repos']}/"
        f"{status_data['expected_repos']} repos processed"
    )

    return extraction_succeeded




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
