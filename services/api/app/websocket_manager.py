from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[WebSocket, str] = {}

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket, username: str) -> None:
        await websocket.accept()
        self._connections[websocket] = username

    def disconnect(self, websocket: WebSocket) -> str | None:
        return self._connections.pop(websocket, None)

    async def broadcast(self, message: dict) -> int:
        failed = 0
        for websocket in list(self._connections.keys()):
            try:
                await websocket.send_json(message)
            except Exception:
                failed += 1
                self.disconnect(websocket)
        return failed
