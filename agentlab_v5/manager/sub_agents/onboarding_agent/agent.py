import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent
from google.adk.memory.types import MemoryType
import logging
from ...tools.tools import claude_web_search
from google.adk.session import Session
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

def setup_logging():
    """Configure logging"""
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('onboarding.log'),
                logging.StreamHandler()
            ]
        )
    return logging.getLogger(__name__)

logger = setup_logging()

dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)  # loads ANTHROPIC_API_KEY from .env
# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to the agentlab_v5 directory and get config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "config.yaml")
cfg = yaml.safe_load(open(config_path))

# Create Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class OnboardingAgent(Agent):
    """
    Onboarding agent that collects user information and preferences.
    Uses Anthropic to guide the user through the onboarding process.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TIMEOUT = 300
        self.MAX_RETRIES = 3

    def check_onboarding_status(self, session_id):
        """Check if user has completed onboarding"""
        try:
            with open(f'user_sessions/{session_id}.json', 'r') as f:
                data = json.load(f)
                return data.get('onboarding_complete', False)
        except FileNotFoundError:
            return False

    def save_session_data(self, session_id, user_data):
        """Save user session data"""
        try:
            os.makedirs('user_sessions', exist_ok=True)
            with open(f'user_sessions/{session_id}.json', 'w') as f:
                json.dump({
                    'onboarding_complete': True,
                    'user_data': user_data,
                    'timestamp': datetime.now().isoformat()
                }, f)
        except Exception as e:
            logger.error(f"Error saving session data: {str(e)}")
            raise

    async def handle_optional_question(self, conversation, question: str) -> str:
        """Handle optional questions with skip option and timeout"""
        await conversation.send_message(f"{question} (Type 'skip' to skip this question)")
        try:
            response = await asyncio.wait_for(conversation.receive_message(), timeout=self.TIMEOUT)
            if response.lower() == 'skip':
                logger.info(f"User skipped question: {question}")
                return "Not specified"
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Timeout while waiting for response to: {question}")
            await conversation.send_message("I didn't receive a response. Let's skip this question for now.")
            return "Not specified"

    async def handle_required_question(self, conversation, question: str) -> str:
        """Handle required questions with retries and timeout"""
        for attempt in range(self.MAX_RETRIES):
            try:
                await conversation.send_message(question)
                response = await asyncio.wait_for(conversation.receive_message(), timeout=self.TIMEOUT)
                if response.strip():
                    return response
                await conversation.send_message("I didn't catch that. Could you please try again?")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1} for question: {question}")
                if attempt < self.MAX_RETRIES - 1:
                    await conversation.send_message("I didn't receive a response. Let's try again.")
                else:
                    await conversation.send_message("I'll need to skip this question for now. We can come back to it later.")
                    return "Not specified"
        return "Not specified"

    async def handle(self, conversation, memory):
        try:
            # Get session ID
            session_id = conversation.session_id
            if not session_id:
                logger.error("No session ID provided")
                raise ValueError("Session ID is required")

            # Check if already onboarded
            if self.check_onboarding_status(session_id):
                logger.info(f"User {session_id} already completed onboarding")
                stored_data = self.get_stored_user_data(session_id)
                # Update memory with stored data
                self._update_memory(memory, stored_data)
                return stored_data

            # Initialize memory if not exists
            if not isinstance(memory, dict):
                memory = {}
            
            logger.info("Starting onboarding process")
            
            # Greet the user
            await conversation.send_message("Hello! I'm here to help you create a personalized AI prompt. Let's get started!")
            
            # Ask for user's name (required)
            user_name = await self.handle_required_question(
                conversation, 
                "What's your name?"
            )
            logger.info(f"User's name: {user_name}")
            
            # Ask for user's interests (optional)
            user_interests = await self.handle_optional_question(
                conversation,
                "What are your interests?"
            )
            logger.info(f"User's interests: {user_interests}")
            
            # Ask for user's hobbies (optional)
            user_hobbies = await self.handle_optional_question(
                conversation,
                "What are your hobbies?"
            )
            logger.info(f"User's hobbies: {user_hobbies}")
            
            # Ask for user's favorite activities (optional)
            user_favorite_activities = await self.handle_optional_question(
                conversation,
                "What are your favorite activities?"
            )
            logger.info(f"User's favorite activities: {user_favorite_activities}")
            
            # Create user data dictionary
            user_data = {
                "user_name": user_name,
                "user_interests": user_interests,
                "user_hobbies": user_hobbies,
                "user_favorite_activities": user_favorite_activities
            }
            
            # Update memory with user data
            self._update_memory(memory, user_data)
            
            # Save session data
            self.save_session_data(session_id, user_data)
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error in onboarding process: {str(e)}")
            await conversation.send_message("I encountered an error. Let's start over.")
            raise

    def get_stored_user_data(self, session_id):
        """Retrieve stored user data"""
        try:
            with open(f'user_sessions/{session_id}.json', 'r') as f:
                data = json.load(f)
                return data.get('user_data', {})
        except FileNotFoundError:
            logger.error(f"No stored data found for session {session_id}")
            return {}

    def validate_memory_type(self, memory_type):
        """Validate memory type"""
        valid_types = [MemoryType.USER_PROFILE, MemoryType.USER_PREFERENCES]
        if memory_type not in valid_types:
            raise ValueError(f"Invalid memory type: {memory_type}")

    def cleanup_old_sessions(self, max_age_days=30):
        """Clean up old session files"""
        try:
            current_time = datetime.now()
            for filename in os.listdir('user_sessions'):
                if filename.endswith('.json'):
                    filepath = os.path.join('user_sessions', filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if (current_time - file_time).days > max_age_days:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old session file: {filename}")
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {str(e)}")

    def _update_memory(self, memory, user_data: Dict[str, Any]):
        """Update memory with user data"""
        try:
            # Add new user data directly to memory dictionary
            memory[MemoryType.USER_PROFILE] = f"User's name: {user_data['user_name']}"
            memory[MemoryType.USER_PREFERENCES] = {
                "interests": user_data['user_interests'],
                "hobbies": user_data['user_hobbies'],
                "favorite_activities": user_data['user_favorite_activities']
            }
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")
            raise

onboarding_agent = OnboardingAgent(
    name="onboarding_agent",
    model=LiteLlm(model=cfg["model"]),
    instruction="""
    You are a helpful assistant that collects user information and preferences through a structured onboarding process.
    
    Your responsibilities include:
    1. User Information Collection:
       - Collect the user's name (required field)
       - Gather user interests (optional)
       - Learn about user hobbies (optional)
       - Understand user's favorite activities (optional)
    
    2. Question Handling:
       - For required questions (like name):
         * Allow up to 3 retries if the user doesn't provide a valid response
         * Wait up to 5 minutes for each response
         * Provide clear feedback if the response is invalid
       - For optional questions:
         * Allow users to skip by typing 'skip'
         * Wait up to 5 minutes for each response
         * Gracefully handle timeouts by skipping the question
    
    3. Error Handling:
       - Handle timeouts gracefully
       - Provide user-friendly error messages
       - Allow recovery from errors
       - Maintain conversation flow even after errors
    
    4. Memory Management:
       - Store user data with proper memory types:
         * USER_PROFILE for name
         * USER_PREFERENCES for interests, hobbies, and activities
       - Ensure data persistence between sessions
       - Handle memory initialization if needed
    
    5. User Experience:
       - Provide clear instructions for each question
       - Explain the skip option for optional questions
       - Give friendly reminders for required information
       - Maintain a conversational and helpful tone
    
    6. Session Management:
       - Check if user has already completed onboarding
       - Save session data for future reference
       - Handle session resumption if needed
    
    After collecting information:
    - Save all data to memory with appropriate types
    - Return structured data to the manager agent
    - Ensure all required fields are properly filled
    - Handle any missing optional fields gracefully
    """,
    description="A sophisticated onboarding assistant that collects and manages user information with robust error handling and session management capabilities."
)
        
        

