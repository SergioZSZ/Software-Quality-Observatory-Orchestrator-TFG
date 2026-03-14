from pydantic import BaseModel


class RunResponse(BaseModel):
    status: dict
    personal_dir: str | None = None
    
