from ..cruds import soca_conf_fetch, soca_extract_portal
from ..models import SocaResponse, Args
from fastapi import APIRouter, HTTPException, status
import os
from soca_runner.config import BASE_DIR, TOKEN

router = APIRouter()

@router.post("/fetch", response_model= SocaResponse)
async def run_soca(request: Args):
    
    os.makedirs(os.path.join(BASE_DIR,"outputs",request.target), exist_ok=True)
    
    #service 
    response = soca_conf_fetch(BASE_DIR, request.target, request.type, TOKEN)
    
    # si es fetchresponse que la devuelva, si no exepcion
    if response.status["status"]=="success":
        return SocaResponse(status="success",response=response.repos, err= None)

    else:
        if response.status["returncode"]==422:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=response.status)

        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.status)
    


    




@router.post("/portal", response_model= SocaResponse)
async def run_soca(request: Args):
    
    os.makedirs(os.path.join(BASE_DIR,"outputs",request.target), exist_ok=True)
    
    #service
    response = soca_extract_portal(BASE_DIR, request.target)
    
    # si es fetchresponse que la devuelva, si no exepcion
    if response.status["status"]=="success":
        return SocaResponse(status="success")
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.status)
    