import json, pika, time, uuid

from ..config import RABBITMQ_HOST, QUEUE_NAME,RABBITMQ_USER, RABBITMQ_PASSWORD, EVENT_QUEUE, RATE_LIMIT_QUEUE


# intentos de conexion a rabbit hasta que se pueda conectar
def rabbit_connect():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    credentials=credentials,
                    heartbeat=7200,
                    blocked_connection_timeout=7200

                )
            )
            print("RabbitMQ conexion set")
            # colas a usar
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.queue_declare(queue=RATE_LIMIT_QUEUE, durable=True, arguments={"x-max-length": 1})
            channel.queue_declare(queue=EVENT_QUEUE, durable=True)
            channel.queue_declare(queue="soca_repo_done", durable=True)

            return connection

        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready, retrying in 5s...", flush=True)
            time.sleep(5)
            

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
   
import json

def publish_event(target):
    
    message= {
        "event": "soca_finished",
        "target": target
        }

    channel.basic_publish(
        exchange="", routing_key=EVENT_QUEUE,body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2))
    
    
    
def publish_repo_done(target: str, work_type: str, repo_url: str):
    
    message = {
        "target": target,
        "work_type": work_type,
        "repo_url": repo_url,
    }

    channel.basic_publish(
        exchange="", routing_key="soca_repo_done",body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2))