from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import pika
import json
import os
import traceback
import random

RMQSTRING = os.environ['RMQSTRING']

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

        print(' [*] Waiting for messages. To exit press CTRL+C', flush=True)
        channel.start_consuming()

    except Exception as e: print(f"Listener error: {e}", flush=True)

def callback(ch, method, properties, body):
    '''
    Purpose: Processes payment messages from the RabbitMQ 'payment' queue, simulates payment success/failure, and publishes the result to the 'processed' queue
    Parameters: ch, method, properties, body. Provided automatically by pika when a message is received
    Returns: Nothing
    '''
    success = random.random() < 0.9
    data = json.loads(body.decode('utf-8'))

    data["status"] = success
    conn = None
    
    parameters = pika.URLParameters(RMQSTRING)
    try:
        conn = pika.BlockingConnection(parameters)
        channel = conn.channel()

        channel.queue_declare(queue='processed')

        channel.basic_publish(
            exchange='',
            routing_key='processed',
            body=json.dumps(data)
        )
        print(f" [x] Sent '{data}'", flush =True)


    except Exception as error:
        print(f"An error occurred: {error}", flush=True)
        print(traceback.format_exc(), flush=True)
        return error

    finally:
        if conn:
            conn.close()



