from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import pika
import threading
import json
import os
import traceback

RMQSTRING = os.environ['RMQSTRING']


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    Purpose: will call listener on a new thread to start wait for messages in the rabbitmq queue
    Parameters: FastAPI instance
    Returns: Nothing
    '''
    t = threading.Thread(target=listener, daemon=True)
    t.start()
    yield 

def listener():
    '''
    Purpose: will listen for payment queue on rabbitmq
    Parameters: None
    Returns: Nothing
    '''
    parameters = pika.URLParameters(RMQSTRING)
    try:
        conn = pika.BlockingConnection(parameters)
        channel = conn.channel()

        channel.queue_declare(queue='payment')  

        channel.basic_consume(  queue='payment',
                                auto_ack=True,
                                on_message_callback=callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()

    except Exception as e: print(f"Listener error: {e}", flush=True)

def callback(ch, method, properties, body):
    #callback function for when something is in payment queue
    print(f" [x] Received {body}", flush=True)



