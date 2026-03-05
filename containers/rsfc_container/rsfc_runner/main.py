from fastapi import FastAPI
from .routers import functions
from .database import engine, Base


Base.metadata.create_all(bind=engine)


# instancia fastapi y routers
app = FastAPI()
app.include_router(router= functions.router, prefix="/functions", tags=["functions"])



@app.get("/isactive")
async def isactive():
    return {"state":True}