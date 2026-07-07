from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import os, shutil
from uuid import uuid4

ASSESSMENT_RELATIVE_PATH = Path("resqui_summary.json")

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


@dataclass(frozen=True)
class RepositoryPaths:
    project_dir: Path
    active_dir: Path
    staging_root: Path


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


def build_resqui_repository_paths(base_dir: str | Path,target: str,repository_url: str,) -> RepositoryPaths:
    repository = parse_github_repository_url(repository_url)
    project_dir = Path(base_dir) / "outputs" / "resqui" / target

    return RepositoryPaths(
        project_dir=project_dir,
        active_dir=project_dir / repository.file_key,
        staging_root=project_dir / ".staging",
    )



def validate_staged_resqui_assessment(staging_dir: str | Path,) -> Path:
    assessment_path = (Path(staging_dir) / ASSESSMENT_RELATIVE_PATH)

    if not assessment_path.is_file():
        raise RuntimeError(
            "RESQUI did not generate resqui_summary.json")

    return assessment_path



def promote_staged_resqui_results(staging_dir: str | Path,active_dir: str | Path,) -> Path:
    staging_path = Path(staging_dir)
    active_path = Path(active_dir)

    validate_staged_resqui_assessment(staging_path)
    active_path.parent.mkdir(parents=True, exist_ok=True)

    backup_path = active_path.parent / (
        f".{active_path.name}.backup-{uuid4().hex}"
    )
    had_active_result = active_path.exists()

    if had_active_result:
        os.replace(active_path, backup_path)

    try:
        os.replace(staging_path, active_path)
    except Exception:
        if had_active_result and backup_path.exists():
            os.replace(backup_path, active_path)
        raise

    if backup_path.exists():
        shutil.rmtree(backup_path)

    return active_path



def remove_repository_old_results(repository_paths: RepositoryPaths,) -> bool:
    active_dir = repository_paths.active_dir

    if not active_dir.exists():
        return False

    if not active_dir.is_dir():
        raise RuntimeError(
            f"Repository result is not a directory: {active_dir}"
        )

    shutil.rmtree(active_dir)
    return True
