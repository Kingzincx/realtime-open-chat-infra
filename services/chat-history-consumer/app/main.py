from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Response

from .consumer import chat_history_consumer
from .database import close_db, connect_db
from .metrics import render_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_db()
    await chat_history_consumer.start()
    try:
        yield
    finally:
        await chat_history_consumer.stop()
        await close_db()


app = FastAPI(title="Chat History Consumer", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    consumer_status = "running" if chat_history_consumer.running else "stopped"
    return {"status": "ok", "consumer": consumer_status}


@app.get("/metrics")
async def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
