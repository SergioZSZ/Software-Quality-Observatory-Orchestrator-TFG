from pydantic import BaseModel
from typing import Optional, Union
import uuid

class Args(BaseModel):
    repo_url: str


    
class RunResponse(BaseModel):
    status: dict
    personal_dir: str | None = None
    

class JobAccepted(BaseModel):
    job_id: uuid.UUID
    status: str

class JobStatus(BaseModel):
    job_id : uuid.UUID
    status: str
    detail: Optional[Union[str, dict]] = None # detalles o indicadores
    path: str | None = None