from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI, Request

from .kafka_client import kafka_producer
from .metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL
from .realtime import router as realtime_router
from .redis_client import close_redis, connect_redis
from .routes import router as http_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_redis()
    await kafka_producer.start()
    try:
        yield
    finally:
        await kafka_producer.stop()
        await close_redis()


app = FastAPI(title="Realtime Open Chat Infra", version="0.1.0", lifespan=lifespan)
app.include_router(http_router)
app.include_router(realtime_router)


@app.middleware("http")
async def record_http_metrics(request: Request, call_next):
    started_at = time.perf_counter()
    path = request.url.path
    try:
        response = await call_next(request)
    except Exception:
        duration = time.perf_counter() - started_at
        HTTP_REQUESTS_TOTAL.labels(request.method, path, "500").inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(request.method, path).observe(duration)
        raise

    duration = time.perf_counter() - started_at
    route = request.scope.get("route")
    metric_path = getattr(route, "path", path)
    HTTP_REQUESTS_TOTAL.labels(
        request.method,
        metric_path,
        str(response.status_code),
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(request.method, metric_path).observe(duration)
    return response
