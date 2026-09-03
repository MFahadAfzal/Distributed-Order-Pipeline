from fastapi import FastAPI
from database import lifespan, reserve, OrderData, getOrderData
from rabbitmq import publishOrderCreated
app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/order")
async def order(data: OrderData):
    orderId = await reserve(data)
    if isinstance(orderId, int):
        publishOrderCreated(orderId)
    return orderId

@app.get("/information")
def information(orderId):
    data = getOrderData(orderId)
    return data

@app.get("/test")
def test(orderId):
    name = publishOrderCreated(orderId)
    return