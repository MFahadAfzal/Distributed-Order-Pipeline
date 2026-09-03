from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import httpx
import os
import traceback

connection_string = f"{os.environ['DBSTRING']}order_db"

class Item(BaseModel):
    id: int
    amount: int

class OrderData(BaseModel):
    orders: list[Item]


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


async def reserve(data: OrderData):
    '''
    Purpose: To check if the required inventory exists and then to reserve the items
    Parameters: OrderData class
    Returns: On success will return orderId, on failure returns the specific error encountered
    '''
    conn = None
    async with httpx.AsyncClient() as client:
        try:
                with psycopg2.connect(connection_string) as conn:
                    with conn.cursor() as cur:
                        cur.execute("BEGIN;")
                        cur.execute("""
                                        INSERT INTO orders DEFAULT VALUES
                                        RETURNING id;
                                    """)
                        orderId, = cur.fetchone()

                        for i in data.orders:

                            # request to get the products information
                            response = (await client.get(f"{os.environ['INVURL']}information?productId={i.id}"))

                            # Raise an exception for 4xx or 5xx status codes    
                            response.raise_for_status() 

                            response = response.json()

                            #will then reserve item if enough in stock, will raise valueError if not
                            if response[2] >= i.amount:
                                reserving = await client.post(f"{os.environ['INVURL']}reserve", params={"id":i.id, "orderId":orderId, "amount": i.amount})

                                if (reserving.status_code == 400):
                                    raise ValueError("Not enough stock for product")
                                
                                            

                                cur.execute("""
                                                INSERT INTO items (order_id, product_id, amount)
                                                VALUES (%s, %s, %s);
                                            """, (orderId, i.id, i.amount ))
                                    
                            else:
                                raise ValueError("Not enough stock for product")

                        cur.execute("COMMIT;")
                        return orderId

        #release stored data in the case of database function failing or one of the products has insufficient stock
        except httpx.HTTPStatusError as exc:
            await client.post(f"{os.environ['INVURL']}release", params={"orderId": orderId})
            raise HTTPException(
                status_code=exc.response.status_code, 
                detail=f"External API error: {exc}"
            )
        
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503, 
                detail=f"Could not reach external server: {exc}"
            )
        
        except ValueError as error:
            await client.post(f"{os.environ['INVURL']}release", params={"orderId": orderId})
            print(f"Insufficient stock: {error}", flush=True)
            return error

        finally:
            if conn:
                conn.close()


def getOrderData(orderId):
    '''
    Purpose: To get the order status and all product ids and amounts related to the order
    Parameters: The order id
    Returns: When successful tuple of status and products, when failure wil return error
    '''
    status = None
    conn = None
    cur = None
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:

                cur.execute("""
                                SELECT status
                                FROM orders
                                WHERE id = %s;
                            """, [orderId])

                
                result = cur.fetchone()
                if result is not None:
                    status = result[0]

                cur.execute("""
                                SELECT product_id, amount
                                FROM items
                                WHERE order_id = %s;
                            """, [orderId])
                products = cur.fetchall()


            return (status, products)

            
    except Exception as error:
            print(f"An error occurred: {error}", flush=True)
            print(traceback.format_exc(), flush=True)
            return error

    finally:
        if conn:
            conn.close()



