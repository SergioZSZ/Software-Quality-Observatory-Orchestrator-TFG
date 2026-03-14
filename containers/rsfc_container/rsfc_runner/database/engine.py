from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
