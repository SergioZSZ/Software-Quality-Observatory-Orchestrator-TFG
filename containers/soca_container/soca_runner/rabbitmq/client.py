import json, pika, time, uuid

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
            # colas a usar
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.queue_declare(queue=RATE_LIMIT_QUEUE, durable=True, arguments={"x-max-length": 1})

            return connection

        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready, retrying in 5s...", flush=True)
            time.sleep(RABBITMQ_RETRY_DELAY_SECONDS)
            

# conexion a rabbit de manera blocked y abrir canal
connection = rabbit_connect()
channel = connection.channel() 
            
def publish_job(target: str, work_type: str, repo_url: str | None = None):

    # publicamos mensaje
    message = {
        "target": target,
        "work_type": work_type,
        "repo_url": repo_url
    }
    
    # publicamos mensaje (delivery mode 2 = mensaje queno se pierda y sea persistente)
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(message),
                            properties = pika.BasicProperties(delivery_mode=2))


   # channel.close()
   # connection.close()
   

