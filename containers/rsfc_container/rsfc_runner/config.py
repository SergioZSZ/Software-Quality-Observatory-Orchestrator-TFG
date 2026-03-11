import os

FILE_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.abspath(os.path.join(FILE_DIR, ".."))

TOKEN = os.getenv("GITHUB_TOKEN")

DATABASE_URL = os.getenv("DATABASE_URL")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
QUEUE_NAME = "rsfc_jobs"

RATE_LIMIT_QUEUE = "github_rate_limit_rsfc"
RATE_LIMIT_RSFC_ENABLED = os.getenv("RATE_LIMIT_RSFC_ENABLED", "true").lower() == "true"

RETRYABLE_ERRORS = [
    "RemoteDisconnected",   # github cierra peticion por demasiadas conexiones simultaneas/timeout
    "SSLError",             # servidor corta conexion/TSL abortado
    "ConnectionError",      # error general de conexion
    "ProtocolError",        # errores deconexion http
    "ReadTimeout",          # github tardando demasiado
    "ConnectTimeout",       # no se abre conexion tcp a tiempo
    "Timeout",              # base de los timeout
    "EOF occurred in violation of protocol",    # github cortando TSL
    "ChunkedEncodingError"  # respuesta hhtp cortada mientras se descargaba
]

