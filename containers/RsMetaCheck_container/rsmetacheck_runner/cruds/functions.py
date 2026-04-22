import json, os, subprocess
from ..models import RunResponse



def run_command(personal_dir: str, cmd: list[str], input: str | None = None) -> dict:
    try:
        # Ejecutamos RsMetaCheck dentro del directorio personal del repo para dejar
        # todos los artefactos asociados bajo la misma carpeta de salida.
        result = subprocess.run(
            cmd,
            capture_output=True,
            input=input,
            text=True,
            check=True,
            cwd=personal_dir,
            timeout=3600,
        )

        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except subprocess.CalledProcessError as e:
        # Dejamos trazas del subprocess para poder diagnosticar errores del CLI.
        print("STDOUT:", e.stdout, flush=True)
        print("STDERR:", e.stderr, flush=True)
        print("RETURN CODE:", e.returncode, flush=True)

        return {
            "status": "error",
            "returncode": e.returncode,
            "stdout": e.stdout,
            "stderr": e.stderr,
        }


# Generacion del directorio personal por repo dentro del target.
def gen_dir(base_dir, target, repo_url: str) -> str:
    repo_name = repo_url.rstrip("/").split("/")[-1]

    outputs_dir = os.path.join(base_dir, "outputs", "rsmetacheck")
    os.makedirs(outputs_dir, exist_ok=True)

    personal_out = os.path.join(outputs_dir, target, repo_name)
    os.makedirs(personal_out, exist_ok=True)

    return personal_out

# Localiza el JSON de metadata generado por SOCA que corresponde al repo actual.
def find_somef_metadata(base_dir: str, target: str, owner: str, repo_name: str, repo_url: str) -> str:
    metadata_dir = os.path.join(base_dir, "outputs", "soca", target, "metadata")

    # SOCA puede normalizar nombres de repo para el nombre del fichero,
    # por ejemplo reemplazando "." por "-".
    repo_name_normalized = repo_name.replace(".", "-")
    prefix_candidates = [
        f"{owner}_{repo_name}_",
        f"{owner}_{repo_name_normalized}_",
    ]

    # Primer intento: resolver por prefijo de filename, que es el caso normal.
    for filename in os.listdir(metadata_dir):
        if not filename.endswith(".json"):
            continue

        if any(filename.startswith(prefix) for prefix in prefix_candidates):
            return os.path.join(metadata_dir, filename)

    # Fallback por contenido para no depender solo del nombre del fichero.
    for filename in os.listdir(metadata_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(metadata_dir, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        code_repository = ""
        full_name = ""
        name = ""

        if metadata.get("code_repository"):
            code_repository = (
                metadata["code_repository"][0]
                .get("result", {})
                .get("value", "")
            )

        if metadata.get("full_name"):
            full_name = (
                metadata["full_name"][0]
                .get("result", {})
                .get("value", "")
            )

        if metadata.get("name"):
            name = (
                metadata["name"][0]
                .get("result", {})
                .get("value", "")
            )

        # Si el contenido describe el mismo repo, aceptamos ese metadata aunque el
        # nombre del fichero no coincida exactamente con la URL.
        if code_repository == repo_url or full_name == f"{owner}/{repo_name}" or name == repo_name:
            return file_path

    raise FileNotFoundError(
        f"No se encontró el JSON de metadata de SOCA para {owner}_{repo_name} en {metadata_dir}"
    )


def rsmetacheck_runner(base_dir: str, target: str, repo_url: str, token: str | None = None) -> RunResponse:
    name = repo_url.rstrip("/").split("/")[-1]
    owner = repo_url.rstrip("/").split("/")[-2]
    name_owner = f"{owner}_{name}"

    # RsMetaCheck reutiliza el SoMEF de SOCA con --skip-somef para evitar rehacer
    # extracción y llamadas innecesarias a GitHub.
    somef_data = find_somef_metadata(base_dir, target, owner, name, repo_url)

    personal_dir = gen_dir(base_dir, target, repo_url)
    pitfalls_dir = os.path.join(personal_dir, "results", "pitfalls")
    os.makedirs(pitfalls_dir, exist_ok=True)

    # --verbose fuerza la generación del JSON-LD individual incluso en repos sin
    # pitfalls, lo que simplifica el tratamiento uniforme posterior en n8n.
    cmd = [
        "rsmetacheck",
        "--skip-somef",
        "--verbose",
        "--input",
        somef_data,
        "--pitfalls-output",
        os.path.join(personal_dir, "results", "pitfalls"),
        "--analysis-output",
        os.path.join(personal_dir, "results", f"{name_owner}_analysis_results.json"),
    ]

    print(" (RSMT)Repo to process:", repo_url)
    result = run_command(personal_dir, cmd)

    # El llamador decidirá si registrar el fallo o continuar con el siguiente repo.
    if result["status"] == "error":
        return RunResponse(status=result)

    return RunResponse(personal_dir=personal_dir, status=result)
