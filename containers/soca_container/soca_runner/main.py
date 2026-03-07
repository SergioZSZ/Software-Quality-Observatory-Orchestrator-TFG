from fastapi import FastAPI
from .routers import functions

app = FastAPI()

app.include_router(router=functions.router, prefix=("/functions"), tags=["/functions"])


@app.get("/isactive")
async def isactive():
    return {"state":True}