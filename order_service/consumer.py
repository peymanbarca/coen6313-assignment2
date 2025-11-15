# order_service/consumer.py
import os
import asyncio
import aio_pika
import json
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE = "user_events"

mongo_client = AsyncIOMotorClient(MONGO_URL)
orders = mongo_client["orderdb"]["orders"]


async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        body = message.body.decode()
        body = json.loads(body)
        print(f'New message consumed: type: {body.get("type")}, body: {body}')
        if body.get("type") == "user.updated":
            # Update all orders for that user_id for email+address if changed
            user_id = body.get("user_id")
            update = {}
            email_update = False
            address_update = False
            if "email" in body:
                update["email"] = body["email"]
                email_update = True
            if "delivery_address" in body:
                update["delivery_address"] = body["delivery_address"]
                address_update = True
            if update:
                # Update all orders that belong to that user_id
                await orders.update_many({"user_id": user_id}, {"$set": update})
                if email_update:
                    print(f'New email field updated for user_id: {user_id}')
                if address_update:
                    print(f'New delivery address field updated for user_id: {user_id}')


async def main():
    conn = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await conn.channel()
    exch = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.FANOUT)
    q = await channel.declare_queue("", exclusive=True)
    await q.bind(exch)
    await q.consume(handle_message)
    print("Consumer started, awaiting messages...")
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
