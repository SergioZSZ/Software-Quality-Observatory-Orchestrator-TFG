import os

# direcciones usadas
FILE_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.abspath(os.path.join(FILE_DIR, ".."))

# github token
TOKEN = os.getenv("GITHUB_TOKEN")

# inputs
TARGET = os.getenv("TARGET")
TYPE = os.getenv("TYPE")

# variables rabbit (queues)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
QUEUE_NAME = "soca_jobs"
RATE_LIMIT_QUEUE = "github_rate_limit_rsfc"
RATE_LIMIT_SOCA_ENABLED = os.getenv("RATE_LIMIT_SOCA_ENABLED", "false").lower() == "true"
RATE_LIMIT_WAIT_SECONDS = 0.5
FETCH_SETTLE_SECONDS = 5
RABBITMQ_RETRY_DELAY_SECONDS = 5
RABBITMQ_HEARTBEAT_SECONDS = 7200
RABBITMQ_BLOCKED_CONNECTION_TIMEOUT_SECONDS = 7200
RATE_LIMIT_TOKEN_INTERVAL_SECONDS = 5
