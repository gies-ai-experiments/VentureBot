from __future__ import annotations

from datetime import datetime, timezone
import logging
import json
from typing import Iterable, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.websockets import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..database import SessionLocal, get_session
from ..models import ChatMessage, ChatSession, MessageRole, JourneyStage
from ..orchestrator_client import generate_assistant_reply, run_onboarding

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _build_suggested_replies(stage: str, updated_context_json: str) -> List[str]:
    if stage == JourneyStage.IDEA_GENERATION.value:
        try:
            context = json.loads(updated_context_json or "{}")
        except json.JSONDecodeError:
            context = {}
        if context.get("idea_slate"):
            return ["1", "2", "3", "4", "5"]
        return []
    if stage == JourneyStage.VALIDATION.value:
        return ["Proceed to PRD", "Try a different idea"]
    if stage == JourneyStage.PRD.value:
        return ["Generate prompts", "Refine requirements"]
    if stage == JourneyStage.PROMPT_ENGINEERING.value:
        return ["Copy prompt", "Start over"]
    return []


def _fetch_session(db: Session, session_id: str) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )
    return session


def _list_messages(db: Session, session_id: str) -> List[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(db.scalars(stmt))


def _chunk_text(text: str, size: int = 128) -> Iterable[str]:
    text = text or ""
    for start in range(0, len(text), size):
        yield text[start : start + size]


@router.post("/sessions", response_model=schemas.SessionStartResponse, status_code=201)
async def create_session(
    payload: schemas.ChatSessionCreate, db: Session = Depends(get_session)
) -> schemas.SessionStartResponse:
    """
    Create a new chat session.
    
    If auto_start is True (default), the onboarding agent will automatically
    run and its output will be included in the response.
    """
    LOGGER.info("Creating new chat session with title: %s", payload.title)
    session = ChatSession(
        title=payload.title,
        current_stage=JourneyStage.ONBOARDING.value,
        stage_context="{}",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    LOGGER.info("Created session: %s", session.id)
    
    onboarding_message = None
    
    if payload.auto_start:
        # Auto-run the onboarding agent
        LOGGER.info("Auto-starting onboarding for session: %s", session.id)
        try:
            onboarding_output, next_stage, updated_context = await run_onboarding(
                session_id=session.id,
                stored_context_json=session.stage_context or "{}",
            )
            LOGGER.info("Onboarding completed for session %s, next stage: %s", session.id, next_stage)
            
            # Save the onboarding output as an assistant message
            assistant_message = ChatMessage(
                session_id=session.id,
                role=MessageRole.ASSISTANT.value,
                content=onboarding_output,
            )
            db.add(assistant_message)
            
            # Update session with new stage and context
            session.current_stage = next_stage
            session.stage_context = updated_context
            session.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(assistant_message)
            db.refresh(session)
            
            onboarding_message = schemas.ChatMessageRead.model_validate(assistant_message)
            
        except Exception as exc:
            LOGGER.exception(f"Auto-onboarding failed for session {session.id}: {exc}")
            # Session is still created, user can trigger onboarding manually
    
    return schemas.SessionStartResponse(
        session=schemas.ChatSessionRead.model_validate(session),
        onboarding_message=onboarding_message,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=schemas.ChatSessionRead,
)
def get_session_info(session_id: str, db: Session = Depends(get_session)) -> schemas.ChatSessionRead:
    """Get session information including current stage."""
    session = _fetch_session(db, session_id)
    return schemas.ChatSessionRead.model_validate(session)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[schemas.ChatMessageRead],
)
def list_messages(session_id: str, db: Session = Depends(get_session)) -> list[schemas.ChatMessageRead]:
    _fetch_session(db, session_id)
    messages = _list_messages(db, session_id)
    return [schemas.ChatMessageRead.model_validate(message) for message in messages]


async def _process_user_message(
    db: Session, session: ChatSession, content: str
) -> tuple[ChatMessage, ChatMessage, str, str]:
    """
    Process a user message and generate the next stage's response.
    
    This is the core of the human-in-the-loop flow:
    1. Save the user's message
    2. Determine the current stage from session
    3. Run the NEXT stage's agent using context from previous stages
    4. Save and return the assistant's response
    """
    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Message content is empty."
        )

    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER.value,
        content=content.strip(),
    )
    db.add(user_message)
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_message)

    # Build conversation payload for context
    conversation_payload = [
        {"role": message.role, "content": message.content}
        for message in _list_messages(db, session.id)
    ]

    # Get current stage and context from session
    current_stage = session.current_stage or JourneyStage.ONBOARDING.value
    stored_context = session.stage_context or "{}"

    # Generate response - this will run the NEXT stage
    LOGGER.info("Generating response for session %s, current stage: %s", session.id, current_stage)
    reply_text, next_stage, updated_context = await generate_assistant_reply(
        session_id=session.id,
        conversation=conversation_payload,
        current_stage=current_stage,
        stored_context_json=stored_context,
    )
    LOGGER.info("Response generated for session %s, next stage: %s, reply length: %d", session.id, next_stage, len(reply_text))

    # Save assistant response
    assistant_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT.value,
        content=reply_text,
    )
    db.add(assistant_message)
    
    # Update session with new stage and context
    session.current_stage = next_stage
    session.stage_context = updated_context
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assistant_message)
    db.refresh(session)

    return user_message, assistant_message, reply_text, updated_context


@router.post(
    "/sessions/{session_id}/messages",
    response_model=schemas.ChatTurnResponse,
    status_code=201,
)
async def send_message(
    session_id: str, payload: schemas.ChatMessageCreate, db: Session = Depends(get_session)
) -> schemas.ChatTurnResponse:
    """
    Send a user message and get the next stage's response.
    
    The response includes the updated session with the new current_stage,
    allowing the client to track progress through the journey.
    """
    if payload.role != MessageRole.USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only user messages can be submitted to this endpoint.",
        )

    session = _fetch_session(db, session_id)
    user_message, assistant_message, _, updated_context = await _process_user_message(
        db, session, payload.content
    )

    # Refresh session to get updated stage info
    db.refresh(session)
    session_read = schemas.ChatSessionRead.model_validate(session)
    
    suggested_replies = _build_suggested_replies(session_read.current_stage, updated_context)
    assistant_read = schemas.ChatMessageRead.model_validate(assistant_message)
    assistant_read.suggested_replies = suggested_replies

    return schemas.ChatTurnResponse(
        session=session_read,
        user_message=schemas.ChatMessageRead.model_validate(user_message),
        assistant_message=assistant_read,
    )


@router.post(
    "/sessions/{session_id}/restart",
    response_model=schemas.SessionStartResponse,
)
async def restart_journey(
    session_id: str, db: Session = Depends(get_session)
) -> schemas.SessionStartResponse:
    """
    Restart the entrepreneurship journey from the beginning.
    
    This resets the session to the onboarding stage and clears accumulated context.
    Previous messages are preserved for reference.
    """
    session = _fetch_session(db, session_id)
    LOGGER.info("Restarting journey for session: %s", session_id)
    
    # Reset session state
    session.current_stage = JourneyStage.ONBOARDING.value
    session.stage_context = "{}"
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    # Add a system message indicating restart
    restart_notice = ChatMessage(
        session_id=session.id,
        role=MessageRole.SYSTEM.value,
        content="--- Journey restarted ---",
    )
    db.add(restart_notice)
    db.commit()
    
    # Run onboarding again
    try:
        onboarding_output, next_stage, updated_context = await run_onboarding(
            session_id=session.id,
            stored_context_json="{}",
        )
        
        assistant_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.ASSISTANT.value,
            content=onboarding_output,
        )
        db.add(assistant_message)
        
        session.current_stage = next_stage
        session.stage_context = updated_context
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(assistant_message)
        db.refresh(session)
        
        onboarding_message = schemas.ChatMessageRead.model_validate(assistant_message)
        
    except Exception as exc:
        LOGGER.exception(f"Restart onboarding failed for session {session.id}: {exc}")
        onboarding_message = None
        db.refresh(session)
    
    return schemas.SessionStartResponse(
        session=schemas.ChatSessionRead.model_validate(session),
        onboarding_message=onboarding_message,
    )


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket endpoint for real-time chat with stage tracking.
    
    Events sent to client:
    - session_ready: Session info with current stage
    - user_message: Echoed user message
    - assistant_token: Streaming response chunks
    - assistant_message: Complete assistant message
    - stage_update: Current stage in the journey
    - error: Error messages
    """
    await websocket.accept()
    LOGGER.info("WebSocket connection accepted for session: %s", session_id)
    try:
        db = SessionLocal()
        try:
            session = _fetch_session(db, session_id)
        except HTTPException as exc:
            await websocket.send_json({"event": "error", "data": exc.detail})
            await websocket.close(code=1008)
            return

        session_payload = (
            schemas.ChatSessionRead.model_validate(session).model_dump(mode="json")
        )
        await websocket.send_json({"event": "session_ready", "data": session_payload})
        
        while True:
            payload = await websocket.receive_json()
            content = payload.get("content", "")
            try:
                LOGGER.info(f"Processing user message: {content[:50]}...")
                user_message, assistant_message, reply_text, updated_context = await _process_user_message(
                    db, session, content
                )
                LOGGER.info(f"Generated reply (length {len(reply_text)}): {reply_text[:50]}...")
            except HTTPException as exc:
                await websocket.send_json({"event": "error", "data": exc.detail})
                continue
            except Exception as exc:
                LOGGER.exception("Unexpected error processing websocket message: %s", exc)
                await websocket.send_json({"event": "error", "data": "Internal server error"})
                continue

            await websocket.send_json(
                {
                    "event": "user_message",
                    "data": schemas.ChatMessageRead.model_validate(
                        user_message
                    ).model_dump(mode="json"),
                }
            )

            # Stream response in chunks
            for chunk in _chunk_text(reply_text):
                await websocket.send_json({"event": "assistant_token", "data": chunk})

            assistant_payload = schemas.ChatMessageRead.model_validate(
                assistant_message
            )
            assistant_payload.suggested_replies = _build_suggested_replies(
                session.current_stage, updated_context
            )

            await websocket.send_json(
                {
                    "event": "assistant_message",
                    "data": assistant_payload.model_dump(mode="json"),
                }
            )
            
            # Send stage update so client knows current progress
            db.refresh(session)
            await websocket.send_json(
                {
                    "event": "stage_update",
                    "data": {
                        "current_stage": session.current_stage,
                        "session": schemas.ChatSessionRead.model_validate(session).model_dump(mode="json"),
                    },
                }
            )
            
    except WebSocketDisconnect:
        LOGGER.info("WebSocket disconnected for session: %s", session_id)
        await websocket.close()
    finally:
        db.close()
