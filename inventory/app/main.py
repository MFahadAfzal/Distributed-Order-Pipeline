from fastapi import FastAPI
from database import lifespan, reservation, releasing, info, updateStatus

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/reserve")
async def reserve(id: int, orderId: int, amount: int, price: int):
    reservation(id, orderId, amount, price)
    return

@app.post("/release")
async def release(orderId: int):
    releasing(orderId)
    return

@app.post("/status")
async def status(orderId: int, status: str):
    return updateStatus(orderId, status)

@app.get("/information")
async def information(productId: int):
    item = info(productId)
    return item
