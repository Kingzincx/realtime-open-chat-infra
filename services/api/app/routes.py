from typing import Any

from fastapi import APIRouter, Response

from .metrics import render_metrics
from .redis_client import list_online_users
from .realtime import manager

router = APIRouter()


@router.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/online-users")
async def online_users() -> dict[str, Any]:
    return {
        "active_connections": manager.active_count,
        "users": await list_online_users(),
    }


@router.get("/metrics")
async def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
