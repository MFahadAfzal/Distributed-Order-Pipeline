from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
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



async def ordering(data: OrderData):

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
                    cur.execute("""
                                    INSERT INTO items (order_id, product_id, amount)
                                    VALUES (%s, %s, %s);
                                """, (orderId, i.id, i.amount ))
                cur.execute("COMMIT;")
                return orderId
    except Exception as error:
            # 'error' holds the exception object
            print(f"An error occurred: {error}", flush=True)
            print(traceback.format_exc(), flush=True)
            return error