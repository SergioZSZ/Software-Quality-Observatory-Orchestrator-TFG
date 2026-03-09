import os, subprocess
from ..models import RunResponse

# funcion para ejecutar subprocessos
def run_command(personal_dir: str,cmd: list[str], input: str | None = None):
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

    except subprocess.CalledProcessError as e:
       
        print("STDOUT:", e.stdout, flush=True)
        print("STDERR:", e.stderr, flush=True)
        print("RETURN CODE:", e.returncode, flush=True)
        
        return {
            "status": "error",
            "returncode": -1,
            "stdout": e.stdout,
            "stderr": e.stderr
        }


def gen_dir(base_dir, repo_url: str) -> str:
    #guardamos ultima parte de la url
    repo_name = repo_url.rstrip("/").split("/")[-1]
    repo_owner = repo_url.rstrip("/").split("/")[-2]
    
    #creacion direcorios personal del procesamiento
    outputs_dir = os.path.join(base_dir,"outputs","rsfc")
    os.makedirs(outputs_dir, exist_ok=True)

    personal_out = os.path.join(outputs_dir,repo_owner,repo_name)
    os.makedirs(personal_out, exist_ok=True)
    
    return personal_out
    
    
    
    
    
def rfsc_runner(base_dir: str, repo_url: str, token: str | None = None) -> RunResponse:

    if token:
        cmd = ["rsfc","--repo",f"{repo_url}","-t",f"{token}"]
    else: 
        cmd = ["rsfc","--repo",f"{repo_url}"]

    personal_dir = gen_dir(base_dir,repo_url)
    
    print(" (RSFC)Repo to process:", repo_url)
    result = run_command(personal_dir, cmd)
    
    
    # comprobacion de errores(evaluating para rate limit y timeout)
    if result["status"] == "error":

        stderr = (result.get("stderr") or "").lower()

        # detectar rate limit
        if "rate limit" in stderr:
            result["status"]="evaluating"
            return RunResponse(status=result)

        # detectar timeout
        if "timeout" in stderr or "read timed out" in stderr:
            result["status"]="evaluating"
            return RunResponse(status=result)

        # cualquier otro error
        return RunResponse(status=result)

    return RunResponse(personal_dir=personal_dir, status=result)