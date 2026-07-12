from ..models import FetchResponse, PortalResponse
import os, subprocess, time
    
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





def soca_fetch(dir_base: str, target: str, type: str)-> FetchResponse:
    # dirs
    target_dir = os.path.join(dir_base,"outputs","soca",target)
    os.makedirs(target_dir , exist_ok=True)
    
    # ficheror repos
    repos_file = os.path.abspath(os.path.join(target_dir,"repos.txt"))
    print("saving repos file in:", repos_file)

    # mandatos soca
    fetch = ["soca", "fetch","-nf","-nd","-na", "-i", target, "-o", repos_file, f"--{type}"]

    
    result_fetch = run_command(fetch)

    if result_fetch.get("stdout"):
        print(f"SOCA stdout:\n{result_fetch['stdout']}", flush=True)

    if result_fetch.get("stderr"):
        print(f"SOCA stderr:\n{result_fetch['stderr']}", flush=True)

    if result_fetch["status"]=="error":
        return FetchResponse(status=result_fetch)    
    
    time.sleep(5)
    if not os.path.isfile(repos_file):
        return FetchResponse(
            status={
                "status": "error",
                "returncode": 422,
                "stdout": result_fetch.get("stdout", ""),
                "stderr": "No se generó el fichero de repositorios",
            }
        )
    
    return FetchResponse(repos=list_repos(repos_file), status= {"status":"success","returncode":0})





def soca_extract(output_dir: str, url: str)-> PortalResponse:
    # directorios a usar
    metadata_dir = os.path.abspath(output_dir)
    os.makedirs(metadata_dir, exist_ok=True)

    extract_command = [
        "soca",
        "extract-1-repo",
        "-i",
        url,
        "-o",
        metadata_dir,
        "-v",
    ]

    result_extract = run_command(extract_command)

    if result_extract["status"] == "error":
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
    



    
    
    



