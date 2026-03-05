from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..rabbitmq.client import publish_job
from ..models import Args, JobAccepted,JobStatus
from ..database import get_db, Job

import uuid


router = APIRouter()

@router.post("/run")
async def run_rsfc(request: Args, db: Session = Depends(get_db))->JobAccepted:

    
    #guardar job en bbdd y mensaje rabbit
    job_id = uuid.uuid4()
    job = Job(id = job_id, repo_url = request.repo_url)
    

    db.add(job) # crea job
    db.commit() # añade la fila
    db.refresh(job)  # actualiza fila 
    
    # publish rabbit
    publish_job(job_id, request.repo_url)
    
    return JobAccepted(job_id=job.id, status="queued")






# comprobación del estado del job dado
@router.get("/status/{job_id}")
async def get_status(job_id: uuid.UUID, db: Session = Depends(get_db)):

    # si no existe el trabajo excepcion
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    # guardamos respuesta
    response = JobStatus(job_id = job_id, status=job.status, detail=job.detail, path = job.result_path)
    
    return response