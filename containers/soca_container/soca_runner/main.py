from .rabbitmq import publish_job
from .models import SocaResponse
from .cruds import soca_fetch
from soca_runner.config import BASE_DIR, TOKEN
from .repository_state import RepositoryRef, RepositorySnapshot, fetch_current_github_repository_state, parse_github_repository_url, calculate_incremental_repository_changes, write_incremental_repository_change_files,load_consolidated_repository_state
import fcntl, json, os, tempfile
from contextlib import contextmanager
from pathlib import Path


VALID_OWNER_TYPES = {"org", "user"}
STATUS_FILENAME = "status.json"
STATUS_LOCK_FILENAME = "status.lock"




# Construye el inventario consultable y conserva el origen de cada repositorio.
def build_repository_snapshots(
    organization_repositories: list[str],
    extra_repositories: list[str],
    token: str | None,
) -> list[tuple[RepositorySnapshot, str]]:
    repositories_by_key: dict[
        str,
        tuple[RepositoryRef, str],
    ] = {}

    candidates = [
        *(
            (repository, "organization")
            for repository in organization_repositories
        ),
        *(
            (repository, "extra")
            for repository in extra_repositories
        ),
    ]

    for repository_url, source in candidates:
        repository = parse_github_repository_url(repository_url)
        key = repository.comparison_key
        existing = repositories_by_key.get(key)

        # Un extra explícito prevalece sobre el mismo repositorio
        # descubierto desde una organización.
        if existing is None or source == "extra":
            repositories_by_key[key] = (
                repository,
                source,
            )

    snapshots: list[
        tuple[RepositorySnapshot, str]
    ] = []

    for repository, source in repositories_by_key.values():
        snapshot = fetch_current_github_repository_state(
            repository,
            token,
        )
        snapshots.append((snapshot, source))

    return snapshots






def normalize_repository(repository: str) -> str:
    repository = repository.strip().rstrip("/")

    if repository.endswith(".git"):
        repository = repository[:-4]

    return repository


def deduplicate_repositories(repositories: list[str]) -> list[str]:
    result = []
    seen = set()

    for repository in repositories:
        normalized = normalize_repository(repository)

        if not normalized:
            continue

        key = normalized.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(normalized)

    return result


def read_json_environment(name: str) -> list:
    raw_value = os.getenv(name, "[]")

    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in environment variable {name}: {exc}"
        ) from exc

    if not isinstance(value, list):
        raise RuntimeError(
            f"Environment variable {name} must contain a JSON array"
        )

    return value


###### Auxiliares status

def get_status_paths(project):
    project_dir = os.path.join(BASE_DIR, "outputs", "soca", project)
    status_file = os.path.join(project_dir, STATUS_FILENAME)
    lock_file = os.path.join(project_dir, STATUS_LOCK_FILENAME)

    return project_dir, status_file, lock_file


# bloquear acceso al status para que solo un proceso pueda modificarlo
@contextmanager
def acquire_status_lock(project):
    project_dir, status_file, lock_file = get_status_paths(project)
    os.makedirs(project_dir, exist_ok=True)

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


# inicializar status antes de enviar trabajos a los workers

def initialize_status(project, expected_repos):
    status_data = {
        "status": "completed" if expected_repos == 0 else "processing",
        "expected_repos": expected_repos,
        "processed_repos": 0,
        "successful_repos": 0,
        "failed_repos": [],
    }

    with acquire_status_lock(project) as status_file:
        write_status_atomic(status_file, status_data)

# Elimina únicamente los resultados SOCA de un repositorio retirado
def remove_repository_metadata(
    metadata_dir: str | Path,
    repository_url: str,
) -> list[Path]:
    metadata_path = Path(metadata_dir)

    if not metadata_path.exists():
        return []

    repository = parse_github_repository_url(repository_url)
    repository_key = repository.file_key
    removed_files: list[Path] = []

    patterns = (
        f"{repository_key}_*.json",
        f"failed_{repository_key}.json",
    )

    for pattern in patterns:
        for file_path in metadata_path.glob(pattern):
            if not file_path.is_file():
                continue

            file_path.unlink()
            removed_files.append(file_path)

    return removed_files



def main(
    project: str,
    organizations: list[dict] | None = None,
    extra_repositories: list[str] | None = None,
):
    print("** Soca runner started **")

    if not project:
        raise RuntimeError("Project name is required")
    

    organizations = organizations or []
    extra_repositories = extra_repositories or []

    # Evitar una ejecución sin ninguna fuente configurada.
    if not organizations and not extra_repositories:
        raise RuntimeError("At least one organization or extra repository is required")
    
    project_dir = os.path.join(BASE_DIR, "outputs", "soca", project)


    os.makedirs(project_dir, exist_ok=True)

    try:
        organization_repositories = []

        # Obtener repositorios de organizaciones y usuarios.
        for source in organizations:
            owner = str(source.get("org", "")).strip()
            owner_type = str(source.get("type", "")).strip().lower()

            if not owner:
                raise RuntimeError(
                    "Every organization entry must contain an 'org' value"
                )

            if owner_type not in VALID_OWNER_TYPES:
                raise RuntimeError(
                    f"Invalid type '{owner_type}' for '{owner}'. "
                    "Expected 'org' or 'user'."
                )

            print(
                f"**\nFetching repositories from "
                f"{owner_type} '{owner}'...\n"
            )

            # usar un directorio temporal para evitar crear repos.txt por organizacion
            with tempfile.TemporaryDirectory(
                prefix=f"soca_fetch_{owner}_"
            ) as temporary_base_dir:
                response_fetch = soca_fetch(
                    temporary_base_dir,
                    owner,
                    owner_type,
                )

                if response_fetch.status["status"] == "error":
                    raise RuntimeError(
                        f"Soca Fetch Error for '{owner}': "
                        f"{response_fetch.status}"
                    )

                organization_repositories.extend(
                    response_fetch.repos
                )

        # Combinar los repositorios descubiertos con los extras configurados.
        # La función elimina duplicados y consulta su estado actual en GitHub.
        snapshots = build_repository_snapshots(
            organization_repositories=organization_repositories,
            extra_repositories=extra_repositories,
            token=TOKEN,
        )

        # Cargar el estado de la última ejecución completada. Si todavía no
        # existe, se usa un estado vacío y todos los repositorios son nuevos.
        previous_state = load_consolidated_repository_state(
            os.path.join(project_dir, "repository-state.json")
        )

        # Comparar la información actual de GitHub con el estado consolidado.
        changes = calculate_incremental_repository_changes(
            previous_state=previous_state,
            current_snapshots=snapshots,
        )

        # Guardar el inventario completo, los repositorios modificados, los
        # eliminados y el estado pendiente que se consolidará al finalizar.
        write_incremental_repository_change_files(
            output_directory=project_dir,
            changes=changes,
        )
        # Retirar de la caché SOCA los repositorios archivados,
        # deshabilitados, eliminados o retirados de la configuración.
        metadata_dir = Path(project_dir) / "metadata"

        for repository_url in changes.removed:
            removed_files = remove_repository_metadata(
                metadata_dir=metadata_dir,
                repository_url=repository_url,
            )

            print(
                f"Removed {len(removed_files)} metadata files "
                f"for '{repository_url}'"
            )


        # Procesar únicamente los repositorios nuevos o modificados.
        repositories = changes.updated

        print(
        f"**\n{len(repositories)} repositories require processing "
        f"for project '{project}'\n"
    )

        # inicializar status antes de publicar los trabajos
        initialize_status(
            project=project,
            expected_repos=len(repositories),
        )

        print(
            f"**\nStatus initialized: "
            f"0/{len(repositories)} repositories processed\n"
        )

        # Publicar un trabajo por repositorio.
        for repository in repositories:
            print(f"{repository} sent to worker")

            publish_job(
                project,
                "extract_metadata",
                repository,
            )

        return SocaResponse(
            status="success",
            target=project,
            response=repositories,
            err=None,
        )

    except Exception as exc:
        print(f"Error: {exc}")
        raise RuntimeError(str(exc)) from exc


if __name__ == "__main__":
    project = os.getenv("PROJECT")

    organizations = read_json_environment(
        "ORGANIZATIONS_JSON"
    )

    extra_repositories = read_json_environment(
        "EXTRA_REPOSITORIES_JSON"
    )

    main(
        project=project,
        organizations=organizations,
        extra_repositories=extra_repositories,
    )
