import asyncio
import json
import ssl
import uuid

import websockets


async def receive_until(websocket, predicate, timeout=10):
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise TimeoutError("timed out waiting for expected WebSocket message")
        message = json.loads(await asyncio.wait_for(websocket.recv(), timeout=remaining))
        if predicate(message):
            return message


async def main():
    ssl_context = ssl.create_default_context(cafile="/certs/ca.crt")
    run_id = uuid.uuid4().hex[:10]
    username_a = f"smoke_a_{run_id}"
    username_b = f"smoke_b_{run_id}"
    content = f"smoke-message-{run_id}"

    async with websockets.connect(
        f"wss://nginx/ws/{username_a}",
        ssl=ssl_context,
    ) as client_a:
        await receive_until(
            client_a,
            lambda event: event.get("type") == "system"
            and event.get("content") == f"{username_a} entrou no chat",
        )

        async with websockets.connect(
            f"wss://nginx/ws/{username_b}",
            ssl=ssl_context,
        ) as client_b:
            await receive_until(
                client_a,
                lambda event: event.get("type") == "system"
                and event.get("content") == f"{username_b} entrou no chat",
            )
            await receive_until(
                client_b,
                lambda event: event.get("type") == "system"
                and event.get("content") == f"{username_b} entrou no chat",
            )

            await client_a.send(json.dumps({"content": content}))

            expected = lambda event: (
                event.get("type") == "message"
                and event.get("username") == username_a
                and event.get("content") == content
            )
            await receive_until(client_a, expected)
            await receive_until(client_b, expected)

    print(
        json.dumps(
            {
                "ok": True,
                "username": username_a,
                "content": content,
            }
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
