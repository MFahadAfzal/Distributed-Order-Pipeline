from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import psycopg2
import os
import traceback

connection_string = f"{os.environ['DBSTRING']}inventory_db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # The 'with' block ensures the connection is closed when finished
        with psycopg2.connect(connection_string) as conn:
            
            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                
                with open("schema.sql", "r", encoding="utf-8") as f:
                    schema_sql = f.read()
            
                # Execute the SQL commands
                cur.execute(schema_sql)

    except Exception as e:
        print(f"Database error occurred: {e}")

    yield 


def reservation(id, orderId, amount):
    '''
    Purpose: to reserve ordered product
    Parameters: The product id, the order id, and the amount wanting to be reserved
    Returns: If successful returns reservation id, if failed then returns exception/error message
    '''
    conn = None
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                #checking if stock is available
                cur.execute("BEGIN;")
                cur.execute("""
                               SELECT amount, reserved 
                               FROM product WHERE id = %s 
                               FOR UPDATE;
                            """, [id])
                
                available, reserved = cur.fetchone()
                #if stock is available then will reserve amount
                if (available >= amount):
                    available = available - amount
                    reserved = reserved + amount

                    #removing amount that is being reserved from product table
                    cur.execute("""
                                    UPDATE product
                                    SET amount = %s, reserved = %s
                                    WHERE id = %s;
                                """, [available, reserved, id])

                    #creating new row in reservations table
                    cur.execute("""
                                    INSERT INTO reservation (order_id, product_id, amount)
                                    VALUES (%s, %s, %s)
                                    RETURNING id;
                                """, [orderId, id, amount])

                    reservationId, = cur.fetchone()

                    cur.execute("COMMIT;")
                    
                    print("product reserved")
                    return reservationId
                
                else:
                    raise HTTPException(status_code=400, detail="Not enough product")
                
    except HTTPException:
        raise

    except Exception as error:
        # 'error' holds the exception object
        print(f"An error occurred: {error}", flush=True)
        print(traceback.format_exc(), flush=True)
        return error
    
    finally:
         if conn:
              conn.close()


def confirmation(orderId):
    '''
    Purpose: To update the database to show the order has been confirmed
    Parameters: the order id
    Returns: If successful returns a dict containing the order id and updated status, if failed then returns exception/error message
    '''
    conn = None
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                                UPDATE reservation
                                SET status = %s
                                where order_id = %s;
                            """, ("payment_successful", orderId))
                cur.execute("COMMIT;")
                return {"id": orderId, "status": "payment_successful"}
            
    except Exception as error:
        print(f"An error occurred: {error}", flush=True)
        print(traceback.format_exc(), flush=True)
        return error

    finally:
         if conn:
              conn.close()




def releasing(orderId):
    """
    Purpose: To delete rows from reservation table and readjust amount in product table
    Parameters: The order id
    Return: The order id on success, the error on failure
    """
    conn = None
    try:
        with psycopg2.connect(connection_string) as conn:
                    with conn.cursor() as cur:
                        cur.execute("BEGIN;")
                        cur.execute("""
                                        SELECT *
                                        FROM reservation
                                        WHERE order_id = %s;
                                    """, [orderId])

                        products = cur.fetchall()
                        for i in products:
                             # i will be (id, order_id, product_id, amount, status)
                            cur.execute("""
                                            UPDATE product
                                            SET reserved = reserved - %s, amount = amount + %s
                                            WHERE id = %s;
                                        """, [i[3],i[3],i[2]])

                            cur.execute("""
                                            DELETE FROM reservation
                                            WHERE id = %s;
                                        """, [i[0]]) 
                        cur.execute("COMMIT;")
                    

                        return {"id": orderId, "status": "order_cancelled"}


    except Exception as error:
            print(f"An error occurred: {error}", flush=True)
            print(traceback.format_exc(), flush=True)
            return error

    finally:
         if conn:
              conn.close()

def info(productId):
    """
    Purpose: getting info about product
    Parameters: the product id
    Returns: tuple of product info or error
    """
    conn = None
    try:
        with psycopg2.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                                    SELECT *
                                    FROM product
                                    WHERE id = %s
                                """, [productId])
                    item = cur.fetchone()
                    return item

    except Exception as error:
        print(f"An error occurred: {error}", flush=True)
        print(traceback.format_exc(), flush=True)
        return error
    
    finally:
         if conn:
              conn.close()