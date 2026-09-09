from fastapi import FastAPI

app = FastAPI()


@app.post("/health")
async def health():
    return {"status": "ok"}

@app.post("/process")
async def health():
    return {"status": "ok"}