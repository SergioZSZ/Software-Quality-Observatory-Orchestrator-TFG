import time, pika
from ..config import RATE_LIMIT_QUEUE
from ..rabbitmq import rabbit_connect


def token_generator():
    # apertura de canal y apertura de la cola y conexion
    connection = rabbit_connect()
    channel = connection.channel()
    channel.queue_declare(queue=RATE_LIMIT_QUEUE, durable=True, arguments={"x-max-length": 1})

    # envío de tokens a la cola cada 3 segundos
    while True:
        channel.basic_publish(exchange="", routing_key=RATE_LIMIT_QUEUE, body="token")
        
        print(f"token sent", flush=True)
        time.sleep(3)  # intervalo entre requests 

if __name__ == "__main__":
    token_generator()