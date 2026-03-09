from ..models import FetchResponse, PortalResponse
import os, subprocess
    
# funcion para ejecutar subprocessos
def run_command(cmd: list[str], input: str | None = None):
    try:
        result=subprocess.run(
            cmd,
            capture_output=True,
            input=input,
            text=True,
            check=True
        )
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "returncode": e.returncode,
            "stdout": e.stdout,
            "stderr": e.stderr
        }
        



#listado de repos para vuelta json
def list_repos(repos_file: str)->list[str]:
    repos: list[str] = []
    
    with open(repos_file, "r", encoding="utf-8") as f:
        for line in f:
            repos.append(line.strip())
    return repos





def soca_fetch(dir_base: str, target: str, type: str, token: str | None = None)-> FetchResponse:
    # dirs
    target_dir = os.path.join(dir_base,"outputs","soca",target)
    os.makedirs(target_dir , exist_ok=True)
    
    # ficheror repos
    repos_file = os.path.abspath(os.path.join(target_dir,"repos.txt"))

    # mandatos soca
    fetch = ["soca", "fetch", "-i", target, "-o", repos_file, f"--{type}"]

    
    result_fetch = run_command(fetch)
    if result_fetch["status"]=="error":
        return FetchResponse(status=result_fetch)    
    
    if os.path.getsize(repos_file) == 0:
        return FetchResponse(status={
            "status": "error",
            "returncode": 422,
            "stdout": "",
            "stderr": "No se generó el fichero con los repositorios o está vacío"
        })
    
    return FetchResponse(repos=list_repos(repos_file), status= {"status":"success","returncode":0})





def soca_extract(dir_base: str, target: str, url: str)-> PortalResponse:
    # directorios a usar
    target_dir = os.path.join(dir_base,"outputs","soca",target)
    dir_metadata = os.path.abspath(os.path.join(target_dir,"metadata"))
    
    
    # mandato soca
    extract = ["soca", "extract-1-repo", "-i", url, "-o", dir_metadata]
    
    # mandatos a orquestar
    
    result_extract =run_command(extract)
    if result_extract["status"]=="error":
        return PortalResponse(status=result_extract) 

    return PortalResponse(status={"status":"success", "returncode":0})





def soca_portal(dir_base: str, target: str)-> PortalResponse:
    # directorios a usar
    target_dir = os.path.join(dir_base,"outputs","soca",target)
    dir_metadata = os.path.abspath(os.path.join(target_dir,"metadata"))
    dir_portal = os.path.abspath(os.path.join(target_dir,"portal"))
    
    
    # mandato soca
    portal = ["soca", "portal", "-i", dir_metadata, "-o", dir_portal]
    
    # mandato 
    result_portal =run_command(portal)
    if result_portal["status"]=="error":
        return PortalResponse(status=result_portal)

    return PortalResponse(status={"status":"success", "returncode":0})
    



    
    
    



