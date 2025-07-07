import chainlit as cl
import os
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
ADK_SERVER_URL = os.getenv("ADK_BACKEND_URL", "http://localhost:8000")
APP_NAME = "manager"

class VentureBotSession:
    """Manages VentureBot session state and API communication"""
    
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
    
    def send_message_stream(self, message: str) -> tuple[bool, str]:
        """Send message to ADK agent and get streaming response"""
        if not self.session_created:
            return False, "Session not created"
            
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
                return True, self._parse_streaming_response(response)
            else:
                return False, f"API Error: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def _parse_streaming_response(self, response) -> str:
        """Parse SSE streaming response from ADK"""
        streaming_text = ""
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                    if event_data.get("content") and event_data["content"].get("parts"):
                        for part in event_data["content"]["parts"]:
                            if part.get("text") and event_data["content"].get("role") == "model":
                                new_text = part["text"]
                                if event_data.get("partial", False):
                                    streaming_text += new_text
                                else:
                                    streaming_text = new_text
                except json.JSONDecodeError:
                    continue
        
        return streaming_text.strip() if streaming_text.strip() else "I processed your request but have no text response."

# Global session instance
venture_session = VentureBotSession()

@cl.on_chat_start
async def start():
    """Initialize chat session when user connects"""
    import time
    
    # Generate unique IDs
    venture_session.user_id = f"user_{int(time.time())}"
    venture_session.session_id = f"session_{int(time.time())}"
    
    # Set user session data
    cl.user_session.set("venture_session", venture_session)
    
    # Welcome message with loading
    loading_msg = cl.Message(content="🚀 **Initializing VentureBots...**\n\nSetting up your AI entrepreneurship coaching session...")
    await loading_msg.send()
    
    # Create backend session
    success, message = venture_session.create_session()
    
    if success:
        # Update loading message
        loading_msg.content = "✅ **VentureBots Ready!**\n\nConnecting you with our AI coaches..."
        await loading_msg.update()
        
        # Send initial greeting to trigger onboarding
        success, response = venture_session.send_message_stream("hi")
        
        if success and response:
            # Send the onboarding response
            onboarding_msg = cl.Message(
                content=response,
                author="VentureBot"
            )
            await onboarding_msg.send()
        else:
            # Fallback welcome message
            welcome_msg = cl.Message(
                content="""👋 **Welcome to VentureBots!**

I'm your AI entrepreneurship coach, ready to help you:
- 💡 **Generate innovative business ideas**
- ✅ **Validate your concepts** 
- 📋 **Develop product strategies**
- 🎯 **Craft effective prompts**

Let's start your entrepreneurial journey! Tell me about your interests or share an idea you'd like to explore.""",
                author="VentureBot"
            )
            await welcome_msg.send()
    else:
        # Error creating session
        error_msg = cl.Message(
            content=f"❌ **Connection Failed**\n\n{message}\n\n💡 **Troubleshooting:**\n• Check if the backend server is running\n• Verify your connection\n• Try refreshing the page",
            author="System"
        )
        await error_msg.send()

@cl.on_message
async def handle_message(message: cl.Message):
    """Handle incoming user messages"""
    venture_session = cl.user_session.get("venture_session")
    
    if not venture_session or not venture_session.session_created:
        error_msg = cl.Message(
            content="❌ Session not properly initialized. Please refresh the page.",
            author="System"
        )
        await error_msg.send()
        return
    
    # Show typing indicator
    async with cl.Step(name="thinking", type="run") as step:
        step.output = "🤔 Your AI coach is analyzing your message..."
        
        # Send message to backend
        success, response = venture_session.send_message_stream(message.content)
        
        if success:
            step.output = "✅ Response ready!"
        else:
            step.output = f"❌ Error: {response}"
    
    if success:
        # Send AI response
        ai_msg = cl.Message(
            content=response,
            author="VentureBot"
        )
        await ai_msg.send()
    else:
        # Send error message
        error_msg = cl.Message(
            content=f"❌ **Connection Error**\n\n{response}\n\n🔄 Try sending your message again or refresh the page.",
            author="System"
        )
        await error_msg.send()

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
            markdown_description="**🚀 VentureBots Entrepreneurship Coach**\n\nYour AI-powered guide for startup success",
            icon="🚀",
        )
    ]

# Optional: Add custom CSS styling
@cl.on_settings_update
async def setup_agent(settings):
    """Handle settings updates if needed"""
    pass

if __name__ == "__main__":
    # This allows running with `python chainlit_app.py`
    import chainlit.cli
    chainlit.cli.run_chainlit(__file__)