import os

FILE_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.abspath(os.path.join(FILE_DIR, ".."))

TOKEN = os.getenv("GITHUB_TOKEN")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
QUEUE_NAME = "soca_jobs"
RATE_LIMIT_QUEUE = "github_rate_limit_rsfc"
RATE_LIMIT_SOCA_ENABLED = os.getenv("RATE_LIMIT_SOCA_ENABLED", "false").lower() == "true"