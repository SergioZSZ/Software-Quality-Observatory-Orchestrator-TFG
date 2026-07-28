from pathlib import Path
import subprocess, os
from ..models import RunResponse
from ..repository_state import parse_github_repository_url
from ..safe_logging import sanitize_data, sanitize_text
from ..config import OUTPUTS_ROOT, RSFC_COMMAND_TIMEOUT_SECONDS, RETRYABLE_ERRORS

# funcion para ejecutar subprocessos
def run_command(personal_dir: str,cmd: list[str], input: str | None = None, env: dict | None = None)-> dict:
    try:
        result=subprocess.run(
            cmd,
            capture_output=True,
            input=input,
            text=True,
            check=True,
            cwd= personal_dir,
            timeout=RSFC_COMMAND_TIMEOUT_SECONDS,
            env=env
        )
        
        #print("STDOUT:", result.stdout, flush=True)
        #print("STDERR:", result.stderr, flush=True)
        #print("RETURN CODE:", result.returncode, flush=True)
    
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "error",
            "returncode": -1,
            "stdout": sanitize_text(exc.stdout or ""),
            "stderr": (
                f"TimeoutExpired after {exc.timeout} seconds\n"
                f"{sanitize_text(exc.stderr or '')}"
            )
        }

    except subprocess.CalledProcessError as e:

        error_text = f"{e.stdout}\n{e.stderr}"
        retryable = any(err in error_text for err in RETRYABLE_ERRORS)

        # solo imprimimos si NO es retryable
        if not retryable:
            print("STDOUT:", sanitize_text(e.stdout), flush=True)
            print("STDERR:", sanitize_text(e.stderr), flush=True)
            print("RETURN CODE:", e.returncode, flush=True)
        
        return sanitize_data({
            "status": "error",
            "returncode": -1,
            "stdout": e.stdout,
            "stderr": e.stderr
        })

    


def find_soca_metadata(
    repo_url: str,
    target: str | None,
    outputs_root: str | Path | None = None,
) -> Path | None:
    if not target:
        return None

    repository = parse_github_repository_url(repo_url)
    base_outputs = Path(outputs_root) if outputs_root is not None else OUTPUTS_ROOT
    metadata_dir = base_outputs / "soca" / target / "metadata"

    if not metadata_dir.exists():
        return None

    metadata_files = sorted(
        metadata_dir.glob(f"{repository.file_key}_*.json"),
        key=lambda metadata_path: metadata_path.stat().st_mtime,
    )
    if not metadata_files:
        return None

    return metadata_files[-1]


def build_rsfc_command(
    repo_url: str,
    token: str | None = None,
    target: str | None = None,
    outputs_root: str | Path | None = None,
) -> list[str]:
    cmd = ["rsfc", "--repo", repo_url]
    metadata_path = find_soca_metadata(repo_url, target, outputs_root)

    if metadata_path:
        cmd.extend(["--metadata", str(metadata_path)])

    if token:
        cmd.extend(["-t", token])

    return cmd


def rfsc_runner(output_dir: str, repo_url: str, token: str | None = None, target: str | None = None) -> RunResponse:
    cmd = build_rsfc_command(repo_url, token, target)
        

    personal_dir = Path(output_dir)
    personal_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()

    if target:
        env["SQOO_SOCA_TARGET"] = target
        
    print(" (RSFC)Repo to process:", repo_url)
    result = run_command(personal_dir, cmd, env=env)
    
    
    # comprobacion de errores(evaluating para rate limit y timeout) en worker
    if result["status"] == "error":

        return RunResponse(status=result)

    return RunResponse(personal_dir=str(personal_dir), status=result)
