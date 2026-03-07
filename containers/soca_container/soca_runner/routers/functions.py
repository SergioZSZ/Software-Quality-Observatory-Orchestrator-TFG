from ..cruds import soca_conf_fetch, soca_extract_portal
from ..rabbitmq import publish_job
from ..models import SocaResponse, Args, StatusResponse
from fastapi import APIRouter, HTTPException, status
import os, json
from soca_runner.config import BASE_DIR, TOKEN

router = APIRouter()

@router.post("/run", response_model= SocaResponse)
async def run_soca(request: Args):
    
    os.makedirs(os.path.join(BASE_DIR,"outputs",request.target), exist_ok=True)
    
    #service 
    response_fetch = soca_conf_fetch(BASE_DIR, request.target, request.type, TOKEN)
    
    # si success publicamos job portal y enviamos repos fetcheados
    if response_fetch.status["status"]=="success":
        
        #generación fichero de estado de extracción y generación
        status_file = {
            "target": request.target,
            "status": "queued",
            "detail": None
        }
        
        #creacion fichero status
        status_file_path = os.path.join(BASE_DIR,"outputs",request.target,"status.json")
        
        with open(status_file_path,"w") as f:
            json.dump(status_file,f)
            
            
        # publicando job
        publish_job(request.target)
        
        
            
        return SocaResponse(status="success", target= request.target, response=response_fetch.repos, err= None)
    
    # errores fetch o conf
    else:
        if response_fetch.status["returncode"]==422:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=response_fetch.status)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response_fetch.status)
    


@router.get("/status/{target}",response_model=StatusResponse)
async def get_status(target: str):
    
    status_file_path = os.path.join(BASE_DIR,"outputs",target,"status.json")
    
    with open(status_file_path, "r") as f:
                data = json.load(f)
    
    return StatusResponse(target = data["target"], status = data["status"], detail = data["detail"])
    
    
'''
# run sincrono (sin generacion portal en paralelo)

@router.post("/run", response_model= SocaResponse)
async def run_soca(request: Args):
    
    os.makedirs(os.path.join(BASE_DIR,"outputs",request.target), exist_ok=True)
    
    #service 
    response_fetch = soca_conf_fetch(BASE_DIR, request.target, request.type, TOKEN)
    
    # si success publicamos job portal
    if response_fetch.status["status"]=="success":
                
        response_portal = soca_extract_portal(BASE_DIR, request.target)
        
        # si reponse portal genera le pasamos a n8n los repos para rsfc
        if response_portal.status["status"]=="success":
            return SocaResponse(status="success",response=response_fetch.repos, err= None)
        
        # errores generacion portal
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response_portal.status)
    
    # errores fetch o conf
    else:
        if response_fetch.status["returncode"]==422:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=response_fetch.status)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response_fetch.status)    
'''
    