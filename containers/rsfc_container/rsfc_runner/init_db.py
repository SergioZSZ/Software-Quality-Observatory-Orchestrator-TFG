from .database import engine, Base
from sqlalchemy import text
from .database import engine

def init_db():
    

    #truncamiento
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE jobs RESTART IDENTITY CASCADE"))
        conn.commit()
    
    # levantamiento
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()