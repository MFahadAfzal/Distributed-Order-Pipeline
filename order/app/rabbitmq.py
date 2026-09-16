import asyncio
import pika
import json
import os
import traceback
import httpx
from database import updateOrderStatus


RMQSTRING = os.environ['RMQSTRING']

def publishOrderCreated(data):
    '''
    Purpose: To send message to payment that an order has been created
    Parameters: the order Id
    Returns:
    nothing
    '''
    conn = None

    parameters = pika.URLParameters(RMQSTRING)
    try:
        conn = pika.BlockingConnection(parameters)
        channel = conn.channel()

        channel.queue_declare(queue='payment')

        channel.basic_publish(
            exchange='',
            routing_key='payment',
            body=json.dumps(data)
        )
        print(f" [x] Sent '{data}'")


    except Exception as error:
        print(f"An error occurred: {error}", flush=True)
        print(traceback.format_exc(), flush=True)
        return error

    finally:
        if conn:
            conn.close()

def listener():
    '''
    Purpose: will listen for processed queue on rabbitmq
    Parameters: None
    Returns: Nothing
    '''
    parameters = pika.URLParameters(RMQSTRING)
    try:
        conn = pika.BlockingConnection(parameters)
        channel = conn.channel()

        channel.queue_declare(queue='processed')  

        channel.basic_consume(  queue='processed',
                                auto_ack=True,
                                on_message_callback=callback)

        print(' [*] Waiting for messages. To exit press CTRL+C', flush=True)
        channel.start_consuming()

    except Exception as e: print(f"Listener error: {e}", flush=True)

def callback(ch, method, properties, body):
    '''
    Purpose: Callback function to handle messages from the 'processed' queue
    Parameters: ch, method, properties, body - provided automatically by pika when a message is received
    Returns: Nothing
    '''
    print(f" [x] Received '{body}'")
    data = json.loads(body.decode('utf-8'))

    orderId = data["orderId"]
    status = "payment_successful" if data["status"] else "payment_failed"

    result = asyncio.run(updateOrderStatus(orderId, status))
    print(f" [x] Update result: {result}", flush=True)

