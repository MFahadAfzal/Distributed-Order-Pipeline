import pika
import os
import traceback
RMQSTRING = os.environ['RMQSTRING']

def publishOrderCreated(orderId):
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
            body=str(orderId)
        )
        print(f" [x] Sent '{orderId}'")


    except Exception as error:
        print(f"An error occurred: {error}", flush=True)
        print(traceback.format_exc(), flush=True)
        return error

    finally:
        if conn:
            conn.close()