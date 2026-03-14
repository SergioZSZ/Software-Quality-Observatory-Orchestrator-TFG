from pydantic import BaseModel


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
