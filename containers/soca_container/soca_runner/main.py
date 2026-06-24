from .rabbitmq import publish_job
from .models import SocaResponse
from .cruds import soca_fetch
from soca_runner.config import BASE_DIR

import argparse
import fcntl
import json
import os
import shutil
import tempfile
from contextlib import contextmanager


VALID_OWNER_TYPES = {"org", "user"}
STATUS_FILENAME = "status.json"
STATUS_LOCK_FILENAME = "status.lock"


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
    }

    with acquire_status_lock(project) as status_file:
        write_status_atomic(status_file, status_data)


def main(
    project: str,
    organizations: list[dict] | None = None,
    extra_repositories: list[str] | None = None,
    repos_file: str | None = None,
):
    print("** Soca runner started **")

    if not project:
        raise RuntimeError("Project name is required")

    organizations = organizations or []
    extra_repositories = extra_repositories or []

    project_dir = os.path.join(BASE_DIR, "outputs", "soca", project)
    metadata_dir = os.path.join(project_dir, "metadata")
    output_repos_file = os.path.join(project_dir, "repos.txt")

    # Eliminar únicamente los metadatos antiguos.
    if os.path.exists(metadata_dir):
        print("**\nRemoving old metadata...\n")
        shutil.rmtree(metadata_dir)

    os.makedirs(project_dir, exist_ok=True)

    try:
        repositories = []

        # Compatibilidad opcional con el antiguo --repos.
        if repos_file:
            print("**\nReading repositories from custom repos.txt...\n")

            with open(repos_file, "r", encoding="utf-8") as file:
                repositories.extend(
                    line.strip()
                    for line in file
                    if line.strip()
                )

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

                repositories.extend(response_fetch.repos)

        # Añadir los repositorios definidos manualmente.
        repositories.extend(extra_repositories)

        # Normalizar y eliminar duplicados.
        repositories = deduplicate_repositories(repositories)

        if not repositories:
            raise RuntimeError(
                "No repositories were found for this project"
            )

        # Guardar la lista definitiva del proyecto.
        with open(output_repos_file, "w", encoding="utf-8") as file:
            file.write("\n".join(repositories))
            file.write("\n")

        print(
            f"**\n{len(repositories)} unique repositories found "
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
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repos",
        help="Optional legacy repos.txt path",
        default=None,
    )

    parser.add_argument(
        "--name",
        help="Optional legacy project name",
        default=None,
    )

    args = parser.parse_args()

    project = os.getenv("PROJECT") or args.name

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
        repos_file=args.repos,
    )
