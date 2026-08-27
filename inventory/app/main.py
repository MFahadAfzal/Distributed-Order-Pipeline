from fastapi import FastAPI
from database import lifespan, reservation, confirmation

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