import time, os, json, random, pika, uuid

from .rabbitmq.client import rabbit_connect
from .cruds.functions import soca_extract_portal

from .config import QUEUE_NAME, BASE_DIR



# carga del mensaje de la cola y envío a background
def process_message(ch, method, properties, body):
    try:
        # cargamos mensaje y cambiamos job de string a uuid
        message = json.loads(body.decode())

        target = message["target"]

        status_file_path = os.path.join(BASE_DIR,"outputs", target,"status.json")

        # actualizar estado json a running
        with open(status_file_path, "r") as f:
            data = json.load(f)
            
        data["status"] = "running"
        
        with open(status_file_path, "w") as f:
            json.dump(data, f)
            
            
        print(f"Received job {target}", flush=True)

        # procesamos mensaje
        response = soca_extract_portal(BASE_DIR, target)
            
        
        if response.status["status"] == "error":
            
        # actualizar estado json a error + detail
                
            data["status"] = "error"
            data["detail"] = response.status
            
            with open(status_file_path, "w") as f:
                json.dump(data, f)
            
            print("Portal generation failed:", response.status, flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

    
        data["status"] = "completed"
        data["detail"] = response.status
            
        with open(status_file_path, "w") as f:
            json.dump(data, f)

        print(f"Job {target} completed", flush=True)
        
        #confirmacion de mensaje pocesado para eliminarlo de la cola
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:

        print("Worker error:", e, flush=True)

        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        
        '''
        # si queremos requeue usar requeue y exception 
        ch.basic_ack(delivery_tag=method.delivery_tag, requeue = True)

    except Exception as e:
        # si falla lo metemos en la cola (faltaría revisar si el error es para meter en cola)
        print(f"[{repos_path}] failed, requeueing:", e)
        
        ch.basic_ack(delivery_tag=method.delivery_tag, requeue=True)
        '''
        

        
        
        
        
        
def worker():
    print("** WORKER STARTED **", flush=True)
    
    # definicion de credenciales, la conexion, credenciales y apertura de canal
    connection = rabbit_connect()
    channel = connection.channel()
    
    # verificación de la cola
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # worker recibe 1 trabajo y recibe el siguiente al terminar
    channel.basic_qos(prefetch_count=1)
    
    # escuchar cola queue procesando por callback dado
    channel.basic_consume( queue=QUEUE_NAME, on_message_callback=process_message)
    
    print("Waiting for jobs...", flush=True)

    channel.start_consuming()
    
    
if __name__ == "__main__":
    worker()