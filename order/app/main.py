from fastapi import FastAPI
from database import lifespan, reserve, OrderData

app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/order")
async def order(data: OrderData):
    orderId = await reserve(data)
    return orderId