import asyncio
import os
from typing import AsyncGenerator, Dict, Optional

import chainlit as cl
import requests

API_BASE_URL = os.getenv("VENTUREBOT_API_URL", "http://localhost:8000")


class VentureBotSession:
    def __init__(self) -> None:
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.stage: Optional[str] = None
        self.initial_message: Optional[str] = None

    def create(self) -> bool:
        if not self.user_id:
            return False
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/sessions",
                json={"user_id": self.user_id},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException:
            return False

        payload = response.json()
        self.session_id = payload["session_id"]
        self.stage = payload.get("stage")
        self.initial_message = payload.get("initial_message")
        return True

    async def chat(self, message: str) -> Dict[str, str]:
        if not self.session_id:
            raise RuntimeError("Session is not initialised")
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/chat",
                json={"session_id": self.session_id, "message": message},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return {
                "message": "🚨 Unable to reach the VentureBot API. Please try again shortly.",
                "stage": self.stage or "unknown",
                "error": str(exc),
            }

        payload = response.json()
        self.stage = payload.get("stage", self.stage)
        return payload

    async def stream_message(self, content: str) -> AsyncGenerator[str, None]:
        for char in content:
            yield char
            await asyncio.sleep(0.01)


session = VentureBotSession()


@cl.on_chat_start
async def start_chat():
    welcome = cl.Message(content="", author="VentureBot")
    greeting = (
        "👋 **Welcome to VentureBot!**\n\n"
        "I'm your AI entrepreneurship coach – ready to help you uncover pain-driven products,"
        " validate opportunities, draft PRDs, and craft no-code prompts."
    )
    async for char in session.stream_message(greeting):
        await welcome.stream_token(char)
    await welcome.send()

    session.user_id = f"user_{int(asyncio.get_event_loop().time() * 1000)}"
    if not session.create():
        error = cl.Message(content="", author="VentureBot")
        text = (
            "❌ **Startup systems offline.**\n"
            "I couldn't reach the VentureBot backend. Please ensure the FastAPI server is running and try again."
        )
        async for char in session.stream_message(text):
            await error.stream_token(char)
        await error.send()
        return

    if session.initial_message:
        initial = cl.Message(content="", author="VentureBot")
        async for char in session.stream_message(session.initial_message):
            await initial.stream_token(char)
        await initial.send()


@cl.on_message
async def handle_message(message: cl.Message):
    if not session.session_id:
        warning = cl.Message(content="", author="System")
        async for char in session.stream_message("Session not ready. Please refresh and try again."):
            await warning.stream_token(char)
        await warning.send()
        return

    response_payload = await session.chat(message.content)
    reply = cl.Message(content="", author="VentureBot")
    async for char in session.stream_message(response_payload.get("message", "")):
        await reply.stream_token(char)
    await reply.send()


@cl.on_chat_end
async def end_chat():
    pass


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="venturebot",
            markdown_description="**🚀 VentureBot**\nMulti-agent startup coach powered by CrewAI.",
            icon="🚀",
        )
    ]


if __name__ == "__main__":
    import chainlit.cli

    chainlit.cli.run_chainlit(__file__)
