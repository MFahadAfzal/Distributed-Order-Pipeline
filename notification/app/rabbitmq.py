import pika
import json
import os

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

        channel.queue_declare(queue='notification')  

        channel.basic_consume(  queue='notification',
                                auto_ack=True,
                                on_message_callback=callback)

        print(' [*] Waiting for messages. To exit press CTRL+C', flush=True)
        channel.start_consuming()

    except Exception as e: print(f"Listener error: {e}", flush=True)

def callback(ch, method, properties, body):
    '''
    Purpose: Processes notification messages from the RabbitMQ 'notification' queue
    Parameters: ch, method, properties, body. Provided automatically by pika when a message is received
    Returns: Nothing
    '''
    data = json.loads(body.decode('utf-8'))
    print(f"Notification Received'{data}'", flush=True)

    if data.get("status") is True:
        print(f"Notification: Order {data.get('orderId')} has been successfully processed.", flush=True)
    else:
        print(f"Notification: Order {data.get('orderId')} has failed to process.", flush=True)
