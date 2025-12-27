"""Integration tests for the Chat API endpoints.

These tests verify the full API behavior including database operations
and endpoint responses.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from services.api_gateway.app.models import MessageRole, JourneyStage


class TestHealthcheck:
    """Tests for the health check endpoint."""

    async def test_healthcheck_returns_ok(self, async_client: AsyncClient):
        """Verify /healthz returns status ok."""
        response = await async_client.get("/healthz")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCreateSession:
    """Tests for session creation endpoint."""

    async def test_create_session_without_auto_start(self, async_client: AsyncClient):
        """Verify session creation without auto-starting onboarding."""
        response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Test Session", "auto_start": False}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify session structure
        assert "session" in data
        session = data["session"]
        assert "id" in session
        assert session["title"] == "Test Session"
        assert session["current_stage"] == JourneyStage.ONBOARDING.value
        
        # Without auto_start, no onboarding message
        assert data["onboarding_message"] is None

    async def test_create_session_with_auto_start(self, async_client: AsyncClient):
        """Verify session creation with auto-started onboarding."""
        response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Auto Start Session", "auto_start": True}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify session and onboarding message
        assert "session" in data
        assert "onboarding_message" in data
        assert data["onboarding_message"] is not None
        assert "Welcome to VentureBot" in data["onboarding_message"]["content"]

    async def test_create_session_with_default_title(self, async_client: AsyncClient):
        """Verify session creation works with null title."""
        response = await async_client.post(
            "/api/chat/sessions",
            json={"auto_start": False}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["session"]["title"] is None


class TestGetSession:
    """Tests for session retrieval endpoint."""

    async def test_get_session_info(self, async_client: AsyncClient):
        """Verify session info retrieval."""
        # Create a session first
        create_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Test Session", "auto_start": False}
        )
        session_id = create_response.json()["session"]["id"]
        
        # Get session info
        response = await async_client.get(f"/api/chat/sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["title"] == "Test Session"
        assert data["current_stage"] == JourneyStage.ONBOARDING.value

    async def test_get_nonexistent_session_returns_404(self, async_client: AsyncClient):
        """Verify 404 is returned for non-existent session."""
        response = await async_client.get("/api/chat/sessions/nonexistent-id-12345")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestListMessages:
    """Tests for message listing endpoint."""

    async def test_list_messages_empty_session(self, async_client: AsyncClient):
        """Verify empty message list for new session without auto_start."""
        create_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Test Session", "auto_start": False}
        )
        session_id = create_response.json()["session"]["id"]
        
        response = await async_client.get(f"/api/chat/sessions/{session_id}/messages")
        
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_messages_with_auto_start(self, async_client: AsyncClient):
        """Verify message list includes onboarding message when auto_start is true."""
        create_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Test Session", "auto_start": True}
        )
        session_id = create_response.json()["session"]["id"]
        
        response = await async_client.get(f"/api/chat/sessions/{session_id}/messages")
        
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 1
        assert messages[0]["role"] == MessageRole.ASSISTANT.value

    async def test_list_messages_nonexistent_session_returns_404(
        self, async_client: AsyncClient
    ):
        """Verify 404 for non-existent session."""
        response = await async_client.get(
            "/api/chat/sessions/nonexistent-id/messages"
        )
        
        assert response.status_code == 404


class TestSendMessage:
    """Tests for message sending endpoint."""

    async def test_send_user_message(self, async_client: AsyncClient):
        """Verify sending a user message works correctly."""
        # Create session
        create_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Test Session", "auto_start": False}
        )
        session_id = create_response.json()["session"]["id"]
        
        # Send message
        response = await async_client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={"role": "user", "content": "Hello, VentureBot!"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "session" in data
        assert "user_message" in data
        assert "assistant_message" in data
        
        # Verify user message
        assert data["user_message"]["role"] == "user"
        assert data["user_message"]["content"] == "Hello, VentureBot!"
        
        # Verify assistant response
        assert data["assistant_message"]["role"] == "assistant"
        assert len(data["assistant_message"]["content"]) > 0

    async def test_send_message_updates_session_stage(self, async_client: AsyncClient):
        """Verify sending a message updates the session stage."""
        create_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Test Session", "auto_start": True}
        )
        session_id = create_response.json()["session"]["id"]
        
        response = await async_client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={"role": "user", "content": "My name is John"}
        )
        
        assert response.status_code == 201
        # The mock returns idea_generation stage
        assert response.json()["session"]["current_stage"] == JourneyStage.IDEA_GENERATION.value

    async def test_send_empty_message_returns_400(self, async_client: AsyncClient):
        """Verify empty messages are rejected."""
        create_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Test Session", "auto_start": False}
        )
        session_id = create_response.json()["session"]["id"]
        
        response = await async_client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={"role": "user", "content": "   "}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    async def test_send_non_user_message_returns_400(self, async_client: AsyncClient):
        """Verify only user messages are accepted."""
        create_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Test Session", "auto_start": False}
        )
        session_id = create_response.json()["session"]["id"]
        
        response = await async_client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={"role": "assistant", "content": "I am the assistant"}
        )
        
        assert response.status_code == 400
        assert "user" in response.json()["detail"].lower()


class TestRestartJourney:
    """Tests for journey restart endpoint."""

    async def test_restart_journey(self, async_client: AsyncClient):
        """Verify journey restart works correctly."""
        # Create session with auto_start
        create_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Test Session", "auto_start": True}
        )
        session_id = create_response.json()["session"]["id"]
        
        # Send a message to move to next stage
        await async_client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={"role": "user", "content": "My name is John"}
        )
        
        # Restart journey
        response = await async_client.post(
            f"/api/chat/sessions/{session_id}/restart"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify session is reset to onboarding
        assert data["session"]["current_stage"] == JourneyStage.ONBOARDING.value
        assert data["onboarding_message"] is not None

    async def test_restart_nonexistent_session_returns_404(
        self, async_client: AsyncClient
    ):
        """Verify 404 for non-existent session restart."""
        response = await async_client.post(
            "/api/chat/sessions/nonexistent-id/restart"
        )
        
        assert response.status_code == 404


class TestConversationFlow:
    """Integration tests for full conversation flows."""

    async def test_full_onboarding_flow(self, async_client: AsyncClient):
        """Test a complete onboarding conversation flow."""
        # Create session with auto_start
        create_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Full Flow Test", "auto_start": True}
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["session"]["id"]
        
        # Verify onboarding message was sent
        messages_response = await async_client.get(
            f"/api/chat/sessions/{session_id}/messages"
        )
        assert len(messages_response.json()) == 1
        
        # User introduces themselves
        response = await async_client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={"role": "user", "content": "My name is Alice and I'm interested in AI"}
        )
        assert response.status_code == 201
        
        # Verify messages are accumulating
        messages_response = await async_client.get(
            f"/api/chat/sessions/{session_id}/messages"
        )
        messages = messages_response.json()
        assert len(messages) == 3  # onboarding + user + assistant

    async def test_multiple_sessions_are_isolated(self, async_client: AsyncClient):
        """Verify sessions are isolated from each other."""
        # Create first session
        session1_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Session 1", "auto_start": False}
        )
        session1_id = session1_response.json()["session"]["id"]
        
        # Create second session
        session2_response = await async_client.post(
            "/api/chat/sessions",
            json={"title": "Session 2", "auto_start": True}
        )
        session2_id = session2_response.json()["session"]["id"]
        
        # Send message only to session 1
        await async_client.post(
            f"/api/chat/sessions/{session1_id}/messages",
            json={"role": "user", "content": "Hello from session 1"}
        )
        
        # Verify session 1 has messages
        session1_messages = await async_client.get(
            f"/api/chat/sessions/{session1_id}/messages"
        )
        assert len(session1_messages.json()) == 2  # user + assistant
        
        # Verify session 2 only has onboarding message
        session2_messages = await async_client.get(
            f"/api/chat/sessions/{session2_id}/messages"
        )
        assert len(session2_messages.json()) == 1  # only onboarding
