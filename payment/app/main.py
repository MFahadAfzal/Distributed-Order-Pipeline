from fastapi import FastAPI
from rabbitmq import lifespan
app = FastAPI(lifespan=lifespan)


@app.post("/health")
async def health():
    return {"status": "ok"}

@app.post("/process")
async def health():
    return {"status": "ok"}