from pydantic import BaseModel

class Args(BaseModel):
    target: str
    type: str
    

class SocaResponse(BaseModel):
    status: str
    target: str
    response: list | None = None
    err: str | None
    
    
class FetchResponse(BaseModel):
    repos: list | None = None
    status: dict

class PortalResponse(BaseModel):
    status: dict


class StatusResponse(BaseModel):
    target: str
    status: str
    detail : dict | None = None