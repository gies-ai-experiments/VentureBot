import asyncio
import websockets
import json
import httpx

API_URL = "http://localhost:8000/api/chat/sessions"
WS_URL_BASE = "ws://localhost:8000/api/chat/ws"

async def test_chat():
    # 1. Create a session
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, json={"title": "Test Session", "auto_start": False})
        if response.status_code != 201:
            print(f"Failed to create session: {response.text}")
            return
        session_data = response.json()
        session_id = session_data["session"]["id"]
        print(f"Created session: {session_id}")

    # 2. Connect to WebSocket
    uri = f"{WS_URL_BASE}/{session_id}"
    async with websockets.connect(uri) as websocket:
        # Wait for session_ready
        response = await websocket.recv()
        print(f"Received: {response}")

        # Send a message
        message = {"content": "Hello, VentureBot!"}
        await websocket.send(json.dumps(message))
        print(f"Sent: {message}")

        # Listen for responses
        while True:
            try:
                response = await websocket.recv()
                print(f"Received: {response}")
                data = json.loads(response)
                if data.get("event") == "assistant_message":
                    break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_chat())
