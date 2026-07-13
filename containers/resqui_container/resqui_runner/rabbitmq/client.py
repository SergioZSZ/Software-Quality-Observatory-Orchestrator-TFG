import json, pika, time

from ..config import (
    RABBITMQ_BLOCKED_CONNECTION_TIMEOUT_SECONDS,
    RABBITMQ_HEARTBEAT_SECONDS,
    RABBITMQ_HOST,
    QUEUE_NAME,
    RABBITMQ_PASSWORD,
    RABBITMQ_RETRY_DELAY_SECONDS,
    RABBITMQ_USER,
    RATE_LIMIT_QUEUE,
)

# intentos de conexion a rabbit hasta que se pueda conectar
def rabbit_connect():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    credentials=credentials,
                    heartbeat=RABBITMQ_HEARTBEAT_SECONDS,
                    blocked_connection_timeout=RABBITMQ_BLOCKED_CONNECTION_TIMEOUT_SECONDS

                )
            )
            print("RabbitMQ conexion set")
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.queue_declare(queue=RATE_LIMIT_QUEUE, durable=True, arguments={"x-max-length": 1})

            return connection

        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready, retrying in 5s...", flush=True)
            time.sleep(RABBITMQ_RETRY_DELAY_SECONDS)
            
# definicion de credenciales, conexion a rabbit de manera síncrona y abrir canal
connection = rabbit_connect()
channel = connection.channel()      
            
def publish_job(job_id: str, repo_url: str, target: str, repos_count: int):
    
    # publicamos mensaje
    message = {
        "job_id": job_id,
        "repo_url": repo_url,
        "target": target,
        "repos_count": repos_count
    }
    
    # publicamos mensaje (delivery mode 2 = mensaje queno se pierda y sea persistente)
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(message),
                            properties = pika.BasicProperties(delivery_mode=2))
    
    #channel.close()
    #connection.close()
    
