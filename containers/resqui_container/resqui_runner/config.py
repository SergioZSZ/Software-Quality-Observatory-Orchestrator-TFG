import os

INPUT = os.getenv("INPUT")

FILE_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.abspath(os.path.join(FILE_DIR, ".."))
RESQUI_CONF = os.path.abspath(os.path.join(BASE_DIR,"resqui_runner","configurations","complete_no_rsfc_superlinter.json"))
TOKEN = os.getenv("GITHUB_TOKEN")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
QUEUE_NAME = "resqui_jobs"
RATE_LIMIT_QUEUE = "github_rate_limit_resqui"
RATE_LIMIT_RESQUI_ENABLED = os.getenv("RATE_LIMIT_RESQUI_ENABLED", "true").lower() == "true"

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


