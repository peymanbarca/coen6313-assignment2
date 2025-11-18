import os
import random
from fastapi import FastAPI, Request, Response
import httpx
import asyncio

app = FastAPI(title='API Gateway')

USER_V1 = os.getenv("USER_V1_URL", "http://localhost:8001")
USER_V2 = os.getenv("USER_V2_URL", "http://localhost:8002")
ORDER = os.getenv("ORDER_URL", "http://localhost:8003")
STRANGLER_PROB = float(os.getenv("STRANGLER_PROB", "0.7"))  # fraction to distribute routing to v1

client = httpx.AsyncClient()


def pick_target_user_service():
    r = random.random()
    if r < STRANGLER_PROB:
        return USER_V1
    return USER_V2


@app.api_route("/users", methods=["POST", "PUT", "GET"])
@app.api_route("/users/{path:path}", methods=["POST", "PUT", "GET"])
async def proxy(request: Request, path: str = ""):
    target = pick_target_user_service()
    url = f"{target}{request.url.path}"
    if request.url.query:
        url = url + "?" + request.url.query
    headers = dict(request.headers)

    # Remove host header to avoid mismatch
    headers.pop("host", None)
    body = await request.body()
    resp = await client.request(request.method, url, headers=headers, content=body, timeout=30.0)
    return Response(status_code=resp.status_code, content=resp.content, headers=resp.headers)


@app.api_route("/orders", methods=["POST", "PUT", "GET"])
@app.api_route("/orders/{path:path}", methods=["POST", "PUT", "GET"])
async def order_proxy(request: Request, path: str = ""):
    target = ORDER
    url = f"{target}{request.url.path}"
    if request.url.query:
        url = url + "?" + request.url.query
    headers = dict(request.headers)

    # Remove host header to avoid mismatch
    headers.pop("host", None)
    body = await request.body()
    resp = await client.request(request.method, url, headers=headers, content=body, timeout=30.0)
    return Response(status_code=resp.status_code, content=resp.content, headers=resp.headers)
