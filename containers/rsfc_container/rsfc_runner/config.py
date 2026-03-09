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


