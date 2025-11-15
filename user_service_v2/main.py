import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import aio_pika
import json
from uuid import uuid4

app = FastAPI()
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["userdb"]
users = db["users"]

# We'll create a connection on startup
rabbit_conn = None
rabbit_channel = None
EXCHANGE_NAME = "user_events"


class User(BaseModel):
    user_id: str = None
    email: str
    delivery_address: str


@app.on_event("startup")
async def startup():
    global rabbit_conn, rabbit_channel
    rabbit_conn = await aio_pika.connect_robust(RABBITMQ_URL)
    rabbit_channel = await rabbit_conn.channel()
    await rabbit_channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.FANOUT)


@app.on_event("shutdown")
async def shutdown():
    if rabbit_conn:
        await rabbit_conn.close()


@app.post("/users", status_code=201)
async def create_user(u: User):
    user_id = u.user_id or str(uuid4())
    doc = {"user_id": user_id, "email": u.email, "delivery_address": u.delivery_address}
    await users.insert_one(doc)
    return {"user_id": user_id}


@app.put("/users/{user_id}")
async def update_user(user_id: str, payload: dict):
    res = await users.find_one({"user_id": user_id})
    if not res:
        raise HTTPException(status_code=404, detail="User not found")
    update_fields = {}
    if "email" in payload:
        update_fields["email"] = payload["email"]
    if "delivery_address" in payload:
        update_fields["delivery_address"] = payload["delivery_address"]
    if not update_fields:
        raise HTTPException(status_code=400,
                            detail="No updatable fields sent, either email or delivery_address should be sent")
    await users.update_one({"user_id": user_id}, {"$set": update_fields})

    # publish event
    event = {"type": "user.updated", "user_id": user_id, **update_fields}
    exch = await rabbit_channel.get_exchange(EXCHANGE_NAME)
    await exch.publish(aio_pika.Message(body=json.dumps(event).encode()), routing_key="")
    return {"ok": True, "user_service_version": "v2", "updated": update_fields}
