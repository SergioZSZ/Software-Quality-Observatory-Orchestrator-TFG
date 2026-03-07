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
            
            
            
def publish_job(target: str):
    
    # definicion de credenciales, conexion a rabbit de manera síncrona y abrir canal
    connection = rabbit_connect()
    channel = connection.channel()
    
    # creamos/aseguramos que la cola existe y sea persistente (durable)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # publicamos mensaje
    message = {
        "target": target
    }
    
    # publicamos mensaje (delivery mode 2 = mensaje queno se pierda y sea persistente)
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(message),
                            properties = pika.BasicProperties(delivery_mode=2))

    channel.close()
    connection.close()