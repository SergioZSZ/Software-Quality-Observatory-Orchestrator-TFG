from pathlib import Path
import os, subprocess
from ..models import RunResponse
from resqui_runner.config import RETRYABLE_ERRORS, RESQUI_CONF

# funcion para ejecutar subprocessos
def run_command(personal_dir: str,cmd: list[str], input: str | None = None)-> dict:
    try:
        result=subprocess.run(
            cmd,
            capture_output=True,
            input=input,
            text=True,
            check=True,
            cwd= personal_dir,
            timeout= 3600
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
            "stdout": exc.stdout or "",
            "stderr": (
                f"TimeoutExpired after {exc.timeout} seconds\n"
                f"{exc.stderr or ''}"
            )
        }
    except subprocess.CalledProcessError as e:

        error_text = f"{e.stdout}\n{e.stderr}"
        retryable = any(err in error_text for err in RETRYABLE_ERRORS)

        # solo imprimimos si NO es retryable
        if not retryable:
            print("STDOUT:", e.stdout, flush=True)
            print("STDERR:", e.stderr, flush=True)
            print("RETURN CODE:", e.returncode, flush=True)
        
        return {
            "status": "error",
            "returncode": -1,
            "stdout": e.stdout,
            "stderr": e.stderr
        }


    


    
    
    
def resqui_runner(output_dir: str, repo_url: str, token: str | None = None) -> RunResponse:

    cmd = ["resqui","-c",f"{RESQUI_CONF}","-u",f"{repo_url}", "-o","resqui_summary.json"]
    
    if token:
        cmd.extend(["-t", token])
        
        
    personal_dir = Path(output_dir)
    personal_dir.mkdir(parents=True, exist_ok=True)
    
    print(" (RESQUI)Repo to process:", repo_url)
    result = run_command(personal_dir, cmd)
    
    
    # comprobacion de errores(evaluating para rate limit y timeout) en worker
    if result["status"] == "error":

        return RunResponse(status=result)

    return RunResponse(personal_dir=str(personal_dir), status=result)