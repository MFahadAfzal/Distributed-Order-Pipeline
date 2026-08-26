from contextlib import asynccontextmanager
from fastapi import FastAPI
import psycopg2
import os

connection_string = f"{os.environ['DBSTRING']}inventory_db"
print(connection_string)
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
