import json
import logging
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .events import publish_chat_event
from .metrics import (
    CHAT_ACTIVE_CONNECTIONS,
    CHAT_MESSAGES_TOTAL,
    CHAT_USER_JOINED_TOTAL,
    CHAT_USER_LEFT_TOTAL,
    CHAT_WEBSOCKET_ERRORS_TOTAL,
)
from .redis_client import decrement_user_session, increment_user_session
from .schemas import InboundMessage, OutboundMessage
from .websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()
manager = ConnectionManager()


def normalize_username(username: str) -> str:
    return username.strip()[:80]


def parse_inbound_message(raw: str) -> InboundMessage:
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        decoded = {"content": raw}

    if not isinstance(decoded, dict):
        raise ValueError("payload must be a JSON object")

    return InboundMessage.model_validate(decoded)


async def broadcast(message: OutboundMessage) -> None:
    failures = await manager.broadcast(message.model_dump())
    if failures:
        CHAT_WEBSOCKET_ERRORS_TOTAL.inc(failures)


@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str) -> None:
    normalized_username = normalize_username(username)
    if not normalized_username:
        await websocket.close(code=1008)
        return

    connected = False

    try:
        await register_connection(websocket, normalized_username)
        connected = True
        await announce_join(normalized_username)
        await receive_messages(websocket, normalized_username)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected username=%s", normalized_username)
    except Exception:
        CHAT_WEBSOCKET_ERRORS_TOTAL.inc()
        logger.exception("Unexpected WebSocket error username=%s", normalized_username)
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass
    finally:
        if connected:
            await unregister_connection(websocket, normalized_username)


async def register_connection(websocket: WebSocket, username: str) -> None:
    await manager.connect(websocket, username)
    CHAT_ACTIVE_CONNECTIONS.inc()
    CHAT_USER_JOINED_TOTAL.inc()
    await increment_user_session(username)


async def unregister_connection(websocket: WebSocket, username: str) -> None:
    manager.disconnect(websocket)
    CHAT_ACTIVE_CONNECTIONS.dec()
    CHAT_USER_LEFT_TOTAL.inc()
    await decrement_user_session(username)

    try:
        left_event, _ = await publish_chat_event("user.left", username)
        await broadcast(
            OutboundMessage(
                type="system",
                username=username,
                content=f"{username} saiu do chat",
                timestamp=left_event.timestamp,
            )
        )
    except Exception:
        CHAT_WEBSOCKET_ERRORS_TOTAL.inc()
        logger.exception("Failed to process user.left for %s", username)


async def announce_join(username: str) -> None:
    join_event, _ = await publish_chat_event("user.joined", username)
    await broadcast(
        OutboundMessage(
            type="system",
            username=username,
            content=f"{username} entrou no chat",
            timestamp=join_event.timestamp,
        )
    )


async def receive_messages(websocket: WebSocket, username: str) -> None:
    while True:
        raw_message = await websocket.receive_text()
        try:
            inbound = parse_inbound_message(raw_message)
        except (ValidationError, ValueError) as exc:
            CHAT_WEBSOCKET_ERRORS_TOTAL.inc()
            await websocket.send_json(
                OutboundMessage(
                    type="error",
                    content=str(exc),
                ).model_dump()
            )
            continue

        await accept_chat_message(websocket, username, inbound)


async def accept_chat_message(
    websocket: WebSocket,
    username: str,
    inbound: InboundMessage,
) -> None:
    message_id = str(uuid4())
    event, published = await publish_chat_event(
        "message.sent",
        username,
        {
            "content": inbound.content,
            "message_id": message_id,
            "content_length": len(inbound.content),
        },
    )

    if not published:
        CHAT_WEBSOCKET_ERRORS_TOTAL.inc()
        await websocket.send_json(
            OutboundMessage(
                type="error",
                content="Message could not be accepted because the event pipeline is unavailable",
            ).model_dump()
        )
        return

    CHAT_MESSAGES_TOTAL.inc()
    await broadcast(
        OutboundMessage(
            type="message",
            message_id=message_id,
            username=username,
            content=inbound.content,
            timestamp=event.timestamp,
        )
    )
