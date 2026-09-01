from fastapi import FastAPI
from database import lifespan, reservation, confirmation, releasing, info

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/reserve")
async def reserve(id: int, orderId: int, amount: int):
    reservation(id, orderId, amount)
    return

@app.get("/confirm")
async def confirm(orderId: int):
    confirmation(orderId)
    return

@app.get("/release")
async def release(orderId: int):
    releasing(orderId)
    return

@app.get("/information")
async def information(productId: int):
    item = info(productId)
    return item