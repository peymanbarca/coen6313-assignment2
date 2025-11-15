import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from uuid import uuid4

app = FastAPI()
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["orderdb"]
orders = db["orders"]


class OrderIn(BaseModel):
    items: list
    email: str
    delivery_address: str
    user_id: str


@app.post("/orders", status_code=201)
async def create_order(o: OrderIn):
    order_id = str(uuid4())
    doc = {
        "order_id": order_id,
        "items": o.items,
        "email": o.email,
        "delivery_address": o.delivery_address,
        "user_id": o.user_id,
        "status": "under process"
    }
    await orders.insert_one(doc)
    return {"order_id": order_id}


@app.get("/orders")
async def list_orders(status: str = None):
    q = {}
    if status:
        q["status"] = status
    cursor = orders.find(q)
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc.get("_id"))
        result.append(doc)
    return result


@app.put("/orders/{order_id}/status")
async def update_status(order_id: str, payload: dict):
    if "status" not in payload:
        raise HTTPException(400, "status required")
    res = await orders.update_one({"order_id": order_id}, {"$set": {"status": payload["status"]}})
    if res.matched_count == 0:
        raise HTTPException(404, "order not found")
    return {"updated": True}
