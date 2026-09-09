from fastapi import FastAPI
from database import lifespan, reserve, OrderData, getOrderData
from rabbitmq import publishOrderCreated
app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/order")
async def order(data: OrderData):
    orderId = None
    reservedData = await reserve(data)

    if not isinstance(reservedData, Exception):
        orderId, totalCost = reservedData

        result = getOrderData(orderId)
        if isinstance(result, Exception):
            return {"error": str(result)}

        status, products = result

        orderData = {
            "orderId": orderId,
            "status": status,
            "products": products,
            "cost": totalCost
        }

        publishOrderCreated(orderData)
    else:
        return {"error": str(reservedData)}
    
    return orderId

@app.get("/information")
def information(orderId):
    data = getOrderData(orderId)
    return data

