from ..cruds import soca_fetch,soca_extract,soca_portal
from ..rabbitmq import publish_job
from ..models import SocaResponse, Args, StatusResponse
from fastapi import APIRouter, HTTPException, status
import os, json, shutil
from soca_runner.config import BASE_DIR, TOKEN

router = APIRouter()


@router.post("/run", response_model= SocaResponse)
async def run_soca(request: Args):
    
    os.makedirs(os.path.join(BASE_DIR,"outputs","soca",request.target), exist_ok=True)
    
    #service 
    response_fetch = soca_fetch(BASE_DIR, request.target, request.type, TOKEN)
    
    # caso success
    if response_fetch.status["status"]=="success":
    
        #generación fichero de estado de extracción y generación portal
        metadata_status = {
            "target": request.target,
            "status": "queued",
            "detail": None,
            "repo_count": len(response_fetch.repos),
            "portal_launched": False
        }
        portal_status = {
            "target": request.target,
            "status": "queued",
            "detail": None
        }
        
        #creacion ficheros status
        metadata_status_file = os.path.join(BASE_DIR,"outputs","soca",request.target,"metadata_status.json")
        portal_status_file = os.path.join(BASE_DIR,"outputs","soca",request.target,"portal_status.json")

        with open(metadata_status_file,"w") as f:
            json.dump(metadata_status,f)
            
        with open(portal_status_file,"w") as f:
            json.dump(portal_status,f)
            
        # truncado carpeta del target por metadatos anticuados guardados
        metadata_dir = os.path.join(BASE_DIR, "outputs", "soca", request.target,"metadata")
        if os.path.exists(metadata_dir):
            shutil.rmtree(metadata_dir)
            
        # publicando jobs de repos por cada uno
        for repo in response_fetch.repos:
            publish_job(request.target, "extract_metadata", repo)
        
        
            
        return SocaResponse(status="success", target= request.target, response=response_fetch.repos, err= None)
    
    # errores fetch o conf
    else:
        if response_fetch.status["returncode"]==422:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=response_fetch.status)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response_fetch.status)
    




@router.get("/status-metadata/{target}",response_model=StatusResponse)
async def get_status_metadata(target: str):
    
    os.makedirs(os.path.join(BASE_DIR,"outputs","soca",target), exist_ok=True)
    
    status_file_path = os.path.join(BASE_DIR,"outputs","soca",target,"metadata_status.json")
    try:
        with open(status_file_path, "r") as f:
                    data = json.load(f)
    
        return StatusResponse(target = data["target"], status = data["status"], detail = data["detail"])        

    # intento de lectura mientras esta lockeado
    except json.JSONDecodeError:
        return StatusResponse(target = target, status = "running")        


@router.get("/status-portal/{target}",response_model=StatusResponse)
async def get_status_portal(target: str):
    
    os.makedirs(os.path.join(BASE_DIR,"outputs","soca",target), exist_ok=True)

    status_file_path = os.path.join(BASE_DIR,"outputs","soca",target,"portal_status.json")
    
    with open(status_file_path, "r") as f:
                data = json.load(f)
    
    return StatusResponse(target = data["target"], status = data["status"], detail = data["detail"])
    
    