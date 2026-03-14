from . import engine, Base
from . import engine

def init_db():
    
    # levantamiento
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()