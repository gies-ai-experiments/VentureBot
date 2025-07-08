import chainlit as cl
import os
import requests
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator

# Configuration
ADK_SERVER_URL = os.getenv("ADK_BACKEND_URL", "http://localhost:8000")
APP_NAME = "manager"

class StreamingVentureBotSession:
    """Enhanced VentureBot session with true Chainlit streaming support"""
    
    def __init__(self):
        self.user_id = None
        self.session_id = None
        self.session_created = False
        self.messages = []
    
    def create_session(self) -> tuple[bool, str]:
        """Create a new ADK session"""
        if not self.user_id or not self.session_id:
            return False, "User ID or Session ID not set"
            
        initial_state = {
            "initialized": True,
            "timestamp": datetime.now().isoformat()
        }
        
        url = f"{ADK_SERVER_URL}/apps/{APP_NAME}/users/{self.user_id}/sessions/{self.session_id}"
        payload = {"state": initial_state}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code in [200, 201, 409]:
                self.session_created = True
                return True, "Session created successfully"
            else:
                return False, f"Failed to create session: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    async def send_message_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Send message to ADK agent and yield streaming tokens"""
        if not self.session_created:
            yield "❌ Session not properly initialized"
            return
            
        url = f"{ADK_SERVER_URL}/run_sse"
        payload = {
            "app_name": APP_NAME,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "body": message,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            },
            "streaming": True
        }
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=30)
            if response.status_code == 200:
                async for token in self._parse_streaming_tokens(response):
                    yield token
            else:
                yield f"❌ API Error: {response.text}"
        except requests.exceptions.RequestException as e:
            yield f"❌ Connection error: {str(e)}"
    
    async def _parse_streaming_tokens(self, response) -> AsyncGenerator[str, None]:
        """Parse SSE streaming response and yield individual tokens"""
        full_response = ""
        
        # First, collect the complete response to avoid partial parsing issues
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                    if event_data.get("content") and event_data["content"].get("parts"):
                        for part in event_data["content"]["parts"]:
                            if part.get("text") and event_data["content"].get("role") == "model":
                                full_response = part["text"]
                                        
                except json.JSONDecodeError:
                    continue
        
        # Now stream the complete response character by character
        if full_response.strip():
            for char in full_response:
                yield char
                await asyncio.sleep(0.01)  # Smooth streaming
        else:
            yield "I processed your request but have no text response."

# Global session instance
venture_session = StreamingVentureBotSession()

@cl.on_chat_start
async def start():
    """Initialize chat session when user connects"""
    import time
    
    # IMMEDIATELY send welcome message - no waiting
    welcome_msg = cl.Message(
        content="",
        author="VentureBot"
    )
    
    # Stream welcome message for demo effect
    welcome_text = """👋 **Welcome to VentureBots!**

I'm your AI entrepreneurship coach, ready to help you:
- 💡 **Generate innovative business ideas**
- ✅ **Validate your concepts** 
- 📋 **Develop product strategies**
- 🎯 **Craft effective prompts**

🚀 **Initializing your coaching session...**"""
    
    # Stream the welcome message character by character (optimized for production)
    for char in welcome_text:
        await welcome_msg.stream_token(char)
        await asyncio.sleep(0.01)  # Faster for production
    
    await welcome_msg.send()
    
    # Generate unique IDs
    venture_session.user_id = f"user_{int(time.time())}"
    venture_session.session_id = f"session_{int(time.time())}"
    
    # Set user session data
    cl.user_session.set("venture_session", venture_session)
    
    # Create backend session in background
    success, message = venture_session.create_session()
    
    if success:
        # Update welcome message to show ready status
        status_msg = cl.Message(content="", author="VentureBot")
        status_text = "✅ **Ready to start!** Tell me about your interests or share an idea you'd like to explore."
        
        for char in status_text:
            await status_msg.stream_token(char)
            await asyncio.sleep(0.01)
        
        await status_msg.send()
        
        # Send initial greeting to trigger onboarding (in background)
        onboarding_msg = cl.Message(content="", author="VentureBot")
        
        async for token in venture_session.send_message_stream("hi"):
            await onboarding_msg.stream_token(token)
            
        await onboarding_msg.send()
        
    else:
        # Show error message
        error_msg = cl.Message(content="", author="VentureBot")
        error_text = f"""❌ **Connection Issue**
{message}

💡 **Troubleshooting:**
• Check if the backend server is running
• Verify your connection  
• Try refreshing the page

You can still chat, but responses may be delayed."""
        
        for char in error_text:
            await error_msg.stream_token(char)
            await asyncio.sleep(0.01)
            
        await error_msg.send()

@cl.on_message
async def handle_message(message: cl.Message):
    """Handle incoming user messages with streaming"""
    venture_session = cl.user_session.get("venture_session")
    
    if not venture_session or not venture_session.session_created:
        error_msg = cl.Message(content="", author="System")
        error_text = "❌ Session not properly initialized. Please refresh the page."
        
        for char in error_text:
            await error_msg.stream_token(char)
            await asyncio.sleep(0.01)
        
        await error_msg.send()
        return
    
    # Create response message for streaming
    response_msg = cl.Message(content="", author="VentureBot")
    
    # Stream the response token by token
    async for token in venture_session.send_message_stream(message.content):
        await response_msg.stream_token(token)
    
    # Send the completed message
    await response_msg.send()

@cl.on_chat_end
async def end():
    """Clean up when chat session ends"""
    venture_session = cl.user_session.get("venture_session")
    if venture_session:
        # Could add cleanup logic here if needed
        pass

# Chat settings
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="entrepreneurship",
            markdown_description="**🚀 VentureBots Entrepreneurship Coach**\n\nYour AI-powered guide for startup success with real-time streaming responses.",
            icon="🚀",
        )
    ]

# Optional: Add custom CSS styling
@cl.on_settings_update
async def setup_agent(settings):
    """Handle settings updates if needed"""
    pass

if __name__ == "__main__":
    # This allows running with `python enhanced_chainlit_app.py`
    import chainlit.cli
    chainlit.cli.run_chainlit(__file__)