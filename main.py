"""FastAPI entrypoint for the CrewAI-powered VentureBot service."""
from __future__ import annotations

import os
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from manager.service import VentureBotService


class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., description="Opaque identifier for the end user.")


class CreateSessionResponse(BaseModel):
    session_id: str
    initial_message: str
    stage: str


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier returned during creation.")
    message: str = Field(..., description="Latest message from the user.")


class ChatResponse(BaseModel):
    message: str
    stage: str
    memory: Dict[str, Any]


service = VentureBotService()

app = FastAPI(title="VentureBot CrewAI API", version="2.0.0")

allowed_origins = os.getenv("VENTUREBOT_CORS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Simple readiness probe."""
    return {"status": "ok"}


@app.post("/api/sessions", response_model=CreateSessionResponse)
def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
    payload = service.create_session(request.user_id)
    return CreateSessionResponse(**payload)


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        payload = service.chat(request.session_id, request.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ChatResponse(**payload)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
