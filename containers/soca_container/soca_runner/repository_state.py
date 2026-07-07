import json
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


# Configuración usada para consultar el estado actual de un repositorio en GitHub
GITHUB_API_URL = "https://api.github.com"
GITHUB_TIMEOUT = 30
VALID_REPOSITORY_SOURCES = {"organization", "extra"}


# Representa una URL de repositorio GitHub ya validada y normalizada
@dataclass(frozen=True)
class RepositoryRef:
    url: str
    owner: str
    name: str

    # Devuelve una clave estable para comparar URLs sin distinguir mayúsculas.
    @property
    def comparison_key(self) -> str:
        return self.url.casefold()

    # Devuelve una clave segura para identificar archivos del repositorio
    @property
    def file_key(self) -> str:
        return f"{self.owner}_{self.name}".replace(".", "-")


# Guarda la información ligera que GitHub devuelve para detectar cambios
@dataclass(frozen=True)
class RepositorySnapshot:
    repository: RepositoryRef
    updated_at: str
    archived: bool
    disabled: bool

    # Convierte el snapshot al formato persistido en repository-state.json
    def to_state_entry(
        self,
        source: str,
    ) -> dict[str, Any]:
        if source not in VALID_REPOSITORY_SOURCES:
            raise ValueError(
                f"Invalid repository source: {source}"
            )

        return {
            "updated_at": self.updated_at,
            "source": source,
            "owner": self.repository.owner,
            "name": self.repository.name,
        }


# Agrupa el lote actualizado, el eliminado y el siguiente estado pendiente
@dataclass
class RepositoryChanges:
    updated: list[str]
    removed: list[str]
    pending_state: dict[str, Any]


# Valida una URL GitHub y devuelve sus datos en un formato normalizado
def parse_github_repository_url(value: str) -> RepositoryRef:
    normalized = value.strip().rstrip("/")

    if normalized.endswith(".git"):
        normalized = normalized[:-4]

    parsed = urlparse(normalized)

    if (
        parsed.scheme != "https"
        or parsed.netloc.casefold() != "github.com"
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"Invalid GitHub repository URL: {value}")

    parts = [part for part in parsed.path.split("/") if part]

    if len(parts) != 2:
        raise ValueError(f"Invalid GitHub repository URL: {value}")

    owner, name = parts
    url = f"https://github.com/{owner}/{name}"

    return RepositoryRef(
        url=url,
        owner=owner,
        name=name,
    )


# Lee el último estado consolidado o devuelve un estado vacío en la primera ejecución
def load_consolidated_repository_state(
    state_path: str | Path,
) -> dict[str, Any]:
    path = Path(state_path)

    if not path.exists():
        return {"repositories": {}}

    try:
        with path.open("r", encoding="utf-8") as file:
            state = json.load(file)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in repository state: {path}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"Could not read repository state: {path}"
        ) from exc

    if not isinstance(state, dict):
        raise RuntimeError(
            "Repository state must be a JSON object"
        )

    repositories = state.get("repositories")

    if not isinstance(repositories, dict):
        raise RuntimeError(
            "Repository state must contain a repositories object"
        )

    return state


# Escribe un JSON mediante un temporal para no dejar archivos parciales
def write_json_file_atomically(
    destination: str | Path,
    data: dict[str, Any],
) -> None:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
        ) as temporary_file:
            json.dump(data, temporary_file, indent=2)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, path)

    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()

        raise


# Escribe una lista de líneas de forma atómica y conserva el orden recibido
def write_lines_file_atomically(
    destination: str | Path,
    lines: Iterable[str],
) -> None:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)

    values = list(lines)

    if any("\n" in value or "\r" in value for value in values):
        raise ValueError("Lines cannot contain line breaks")

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
        ) as temporary_file:
            for value in values:
                temporary_file.write(f"{value}\n")

            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, path)

    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()

        raise


# Consulta GitHub y obtiene únicamente los datos necesarios para detectar cambios
def fetch_current_github_repository_state(
    repository: RepositoryRef,
    token: str | None,
) -> RepositorySnapshot:
    headers = {
        "Accept": "application/vnd.github+json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    api_url = (
        f"{GITHUB_API_URL}/repos/"
        f"{repository.owner}/{repository.name}"
    )

    try:
        response = requests.get(
            api_url,
            headers=headers,
            timeout=GITHUB_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not fetch GitHub repository: {repository.url}"
        ) from exc
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid GitHub response for: {repository.url}"
        ) from exc

    updated_at = payload.get("updated_at")
    archived = payload.get("archived")
    disabled = payload.get("disabled")
    html_url = payload.get("html_url")

    if (
        not isinstance(updated_at, str)
        or not isinstance(archived, bool)
        or not isinstance(disabled, bool)
        or not isinstance(html_url, str)
    ):
        raise RuntimeError(
            f"Incomplete GitHub response for: {repository.url}"
        )

    canonical_repository = parse_github_repository_url(html_url)

    return RepositorySnapshot(
        repository=canonical_repository,
        updated_at=updated_at,
        archived=archived,
        disabled=disabled,
    )


# Compara el estado anterior con los snapshots actuales sin modificar archivos
def calculate_incremental_repository_changes(
    previous_state: dict[str, Any],
    current_snapshots: list[
        tuple[RepositorySnapshot, str]
    ],
) -> RepositoryChanges:
    previous_repositories = previous_state["repositories"]

    previous_by_key: dict[
        str,
        tuple[RepositoryRef, dict[str, Any]],
    ] = {}

    for repository_url, entry in previous_repositories.items():
        if not isinstance(repository_url, str):
            raise RuntimeError(
                "Repository state URLs must be strings"
            )

        if not isinstance(entry, dict):
            raise RuntimeError(
                f"Invalid state entry for: {repository_url}"
            )

        if not isinstance(entry.get("updated_at"), str):
            raise RuntimeError(
                f"Missing updated_at for: {repository_url}"
            )

        repository = parse_github_repository_url(repository_url)

        previous_by_key[repository.comparison_key] = (
            repository,
            entry,
        )

    current_by_key: dict[
        str,
        tuple[RepositorySnapshot, str],
    ] = {}

    for snapshot, source in current_snapshots:
        if source not in VALID_REPOSITORY_SOURCES:
            raise ValueError(
                f"Invalid repository source: {source}"
            )

        key = snapshot.repository.comparison_key
        existing = current_by_key.get(key)

        # La inclusión explícita como extra prevalece sobre la organización
        if existing is None or source == "extra":
            current_by_key[key] = (snapshot, source)

    updated: list[str] = []
    pending_repositories: dict[str, Any] = {}

    for key, (snapshot, source) in current_by_key.items():
        previous = previous_by_key.get(key)

        if (
            previous is None
            or previous[1]["updated_at"]
            != snapshot.updated_at
        ):
            updated.append(snapshot.repository.url)

        pending_repositories[snapshot.repository.url] = (
            snapshot.to_state_entry(source)
        )

    removed: list[str] = []

    for key, (repository, _) in previous_by_key.items():
        if key not in current_by_key:
            removed.append(repository.url)

    generated_at = (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )

    return RepositoryChanges(
        updated=updated,
        removed=removed,
        pending_state={
            "generated_at": generated_at,
            "repositories": pending_repositories,
        },
    )


# Guarda el inventario completo, los lotes incrementales y el estado pendiente
def write_incremental_repository_change_files(
    output_directory: str | Path,
    changes: RepositoryChanges,
) -> None:
    output_path = Path(output_directory)

    all_repositories = list(
        changes.pending_state["repositories"].keys()
    )

    write_lines_file_atomically(
        output_path / "repos.txt",
        all_repositories,
    )
    write_lines_file_atomically(
        output_path / "repos-updated.txt",
        changes.updated,
    )
    write_lines_file_atomically(
        output_path / "repos-removed.txt",
        changes.removed,
    )

    # El pending se escribe al final para señalar que las listas ya son válidas.
    write_json_file_atomically(
        output_path / "repository-state.pending.json",
        changes.pending_state,
    )
