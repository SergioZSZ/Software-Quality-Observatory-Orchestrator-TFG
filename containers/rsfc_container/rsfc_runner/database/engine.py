from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from ..config import DATABASE_URL

# postgresql://usuario:password@host:puerto/database

# creación de conexion a la bbdd
engine = create_engine(DATABASE_URL)


# geeneracion de sesiones de acceso a la bbdd
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)





#sesion de la bbdd cada vez que llamado
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()