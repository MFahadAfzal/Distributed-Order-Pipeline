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
    priceCents: int

class OrderData(BaseModel):
    orders: list[Item]


def setupSchema():
    '''
    Purpose: Creates the database schema on first run by executing schema.sql
    Parameters: None
    Returns: Nothing
    '''
    conn = None
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                with open("schema.sql", "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                cur.execute(schema_sql)
    except Exception as e:
        print(f"Database error occurred: {e}")
    finally:
        if conn:
            conn.close()

async def reserve(data: OrderData):
    '''
    Purpose: To check if the required inventory exists and then to reserve the items
    Parameters: OrderData class
    Returns: On success will return orderId, on failure returns the specific error encountered
    '''
    conn = None
    async with httpx.AsyncClient() as client:
        try:
                totalCost = 0
                with psycopg2.connect(connection_string) as conn:
                    with conn.cursor() as cur:
                        cur.execute("BEGIN;")
                        cur.execute("""
                                        INSERT INTO orders DEFAULT VALUES
                                        RETURNING id;
                                    """)
                        orderId, = cur.fetchone()

                        for i in data.orders:
                            totalCost += i.priceCents
                            # request to get the products information
                            response = (await client.get(f"{os.environ['INVURL']}information?productId={i.id}"))

                            # Raise an exception for 4xx or 5xx status codes    
                            response.raise_for_status() 

                            response = response.json()
                            print(f'{response}', flush=True)
                            #will then reserve item if enough in stock, will raise valueError if not
                            if response[2] >= i.amount:
                                reserving = await client.post(f"{os.environ['INVURL']}reserve", params={"id":i.id, "orderId":orderId, "amount": i.amount, "price":i.priceCents})

                                if (reserving.status_code == 400):
                                    raise ValueError("Not enough stock for product")
                                
                                            

                                cur.execute("""
                                                INSERT INTO items (order_id, product_id, amount, price)
                                                VALUES (%s, %s, %s, %s);
                                            """, (orderId, i.id, i.amount, i.priceCents ))
                            
                                    
                            else:
                                raise ValueError("Not enough stock for product")

                        cur.execute("COMMIT;")
                        return (orderId, totalCost)

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

async def updateOrderStatus(orderId, status):
    '''
    Purpose: Updates the order's status in the local database and calls Inventory's /status endpoint to update the corresponding reservation status.
    Parameters: orderId, the order's id. status, the new status to set.
    Returns: On success, dict with id and status. On failure, dict with error or the exception object.
    '''
    conn = None
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                                UPDATE orders
                                SET status = %s
                                WHERE id = %s;
                            """, [status, orderId])

                if cur.rowcount == 0:
                    return {"error": f"No order found for {orderId}"}

                cur.execute("COMMIT;")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.environ['INVURL']}status",
                params={"orderId": orderId, "status": status}
            )
            response.raise_for_status()

        return {"id": orderId, "status": status}

    except Exception as error:
        print(f"An error occurred: {error}", flush=True)
        print(traceback.format_exc(), flush=True)
        return error

    finally:
        if conn:
            conn.close()


def getOrderData(orderId):
    '''
    Purpose: To get the order status and all product ids, amounts, and prices related to the order
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
                if result is None:
                    raise ValueError(f"Order {orderId} not found")
                
                status = result[0]

                cur.execute("""
                                SELECT product_id, amount, price
                                FROM items
                                WHERE order_id = %s;
                            """, [orderId])
                products = cur.fetchall()

                if not products:
                    raise ValueError(f"Order {orderId} not found")

                products = [
                    {"product_id": p[0], "amount": p[1], "price": p[2]}
                    for p in products
                ]
            return (status, products)

            
    except Exception as error:
            print(f"An error occurred: {error}", flush=True)
            print(traceback.format_exc(), flush=True)
            return error

    finally:
        if conn:
            conn.close()



