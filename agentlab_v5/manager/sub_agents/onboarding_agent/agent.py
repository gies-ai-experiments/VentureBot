import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent
import logging
from ...tools.tools import claude_web_search
import json
import asyncio
from typing import Optional, Dict, Any, ClassVar
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
    # Class variables with proper type annotations
    TIMEOUT: ClassVar[int] = 300
    MAX_RETRIES: ClassVar[int] = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            logger.info("Starting onboarding process")
            
            # Greet the user
            await conversation.send_message("Hello! I'm here to help you create a personalized AI prompt. Let's get started!")
            
            # Ask for user's name
            user_name = await self.handle_required_question(
                conversation, 
                "What's your name?"
            )
            logger.info(f"User's name: {user_name}")
            
            # Ask for user's interests
            await conversation.send_message("What are your interests? (This will help us generate better ideas for you)")
            user_interests = await asyncio.wait_for(conversation.receive_message(), timeout=self.TIMEOUT)
            logger.info(f"User's interests: {user_interests}")
            
            # Create user data dictionary
            user_data = {
                "user_name": user_name,
                "user_interests": user_interests
            }
            
            # Return the data to be used by the idea generator
            return user_data
            
        except Exception as e:
            logger.error(f"Error in onboarding process: {str(e)}")
            await conversation.send_message("I encountered an error. Let's start over.")
            raise

onboarding_agent = OnboardingAgent(
    name="onboarding_agent",
    model=LiteLlm(model=cfg["model"]),
    instruction="""
    You are a friendly assistant that collects basic user information to help generate personalized ideas.
    
    Your responsibilities:
    1. Greet the user warmly
    2. Ask for their name
    3. Ask about their interests
    4. Pass this information to the idea generator
    
    Keep the conversation simple and focused on gathering essential information.
    """,
    description="A simple onboarding assistant that collects basic user information to help generate personalized ideas."
)
        
        

