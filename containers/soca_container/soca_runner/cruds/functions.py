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





def soca_conf_fetch(dir_base: str, target: str, type: str, token: str | None = None)-> FetchResponse:
    
    # ficheror repos
    repos_file = os.path.abspath(os.path.join(dir_base,"outputs",target,"repos.txt"))

    # mandatos soca
    conf_soca = ["soca","configure"]    
    conf_somef = ["somef","configure"]
    fetch = ["soca", "fetch", "-i", target, "-o", repos_file, f"--{type}"]

        # respuesta de somef dependiendo de token
    if token:
        conf_somef_input = f"{token}\n\n\n\n\n\n"
    else:
        conf_somef_input = f"\n\n\n\n\n\n"
    
    result_conf_somef = run_command(conf_somef, input = conf_somef_input)
    if result_conf_somef["status"]=="error":
        return FetchResponse(status=result_conf_somef)
    
    result_conf_soca =run_command(conf_soca, input="\n\n\nmytoken\n\n")
    if result_conf_soca["status"]=="error":
        return FetchResponse(status=result_conf_soca)
    
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





def soca_extract_portal(dir_base: str, target: str)-> PortalResponse:
    # directorios a usar
    repos_file = os.path.abspath(os.path.join(dir_base,"outputs",target,"repos.txt"))
    dir_metadata = os.path.abspath(os.path.join(dir_base,"outputs",target,"metadata"))
    dir_portal = os.path.abspath(os.path.join(dir_base,"outputs",target,"portal"))
    
    if os.path.getsize(repos_file) == 0:
        return PortalResponse(status={
            "status": "error",
            "returncode": 1,
            "stdout": "",
            "stderr": "No se generó el fichero con los repositorios o está vacío"
        })
    
    # mandatos soca
    extract = ["soca", "extract", "-i", repos_file, "-o", dir_metadata]
    portal = ["soca", "portal", "-i", dir_metadata, "-o", dir_portal]
    
    # mandatos a orquestar
    
    result_extract =run_command(extract)
    if result_extract["status"]=="error":
        return PortalResponse(status=result_extract) 

    result_portal =run_command(portal)
    if result_portal["status"]=="error":
        return PortalResponse(status=result_portal)

    return PortalResponse(status={"status":"success", "returncode":0})
    



    
    
    



