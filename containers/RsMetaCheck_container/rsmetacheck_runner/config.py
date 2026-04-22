import os

INPUT = os.getenv("INPUT")

FILE_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.abspath(os.path.join(FILE_DIR, ".."))

TOKEN = os.getenv("GITHUB_TOKEN")

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

