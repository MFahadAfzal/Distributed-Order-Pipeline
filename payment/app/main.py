from fastapi import FastAPI
from rabbitmq import listener
from contextlib import asynccontextmanager
import threading

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

app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}

