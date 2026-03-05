import json, pika, time, uuid

from ..config import RABBITMQ_HOST, QUEUE_NAME,RABBITMQ_USER, RABBITMQ_PASSWORD


# intentos de conexion a rabbit hasta que se pueda conectar
def rabbit_connect():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    credentials=credentials
                )
            )
            print("RabbitMQ conexion set")
            return connection

        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready, retrying in 5s...", flush=True)
            time.sleep(5)
            
            
            
def publish_job(job_id: uuid.UUID, repo_url: str):
    
    # definicion de credenciales, conexion a rabbit de manera síncrona y abrir canal
    connection = rabbit_connect()
    channel = connection.channel()
    
    # creamos/aseguramos que la cola existe y sea persistente (durable)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # publicamos mensaje
    message = {
        "job_id": str(job_id),
        "repo_url": repo_url
    }
    
    # publicamos mensaje (delivery mode 2 = mensaje queno se pierda y sea persistente)
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(message),
                            properties = pika.BasicProperties(delivery_mode=2))

    channel.close()