import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent
import logging
from manager.tools.tools import claude_web_search
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
# Navigate up to the VentureBots directory and get config.yaml
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
            # Send the structured onboarding message as shown in the screenshot, introducing VentureBot
            await conversation.send_message(
                """
Welcome to Your AI Product Journey!

Hello and welcome! I'm VentureBot, your AI coach, here to guide you through creating your own AI-powered product. Whether you have a specific idea in mind or you're just starting to explore possibilities, I'm here to help you turn your vision into reality.

Throughout this journey, we'll incorporate important technical concepts from BADM 350 to make your product innovative and competitive. You can call me VentureBot anytime if you have questions or need help!

How I Can Help You

I can assist you with:

• Generating and refining innovative ideas
• Validating your concepts through feasibility assessment
• Developing comprehensive product requirements
• Creating effective prompts for no-code app builders
• Understanding technical concepts like network effects, data-driven value, and more

Getting Started

To begin, I'd love to learn a bit about you:

- What are your interests or hobbies?
- Do you have any specific problems you'd like to solve?
- Are there any particular industries or technologies that interest you?

This information will help me tailor our creative process to your unique goals and interests. Let's get started!"""
            )
            user_response = await asyncio.wait_for(conversation.receive_message(), timeout=self.TIMEOUT)
            logger.info(f"User's onboarding response: {user_response}")

            user_data = {
                "user_profile": user_response
            }
            return user_data  # Immediately hand off to the next agent
        except Exception as e:
            logger.error(f"Error in onboarding process: {str(e)}")
            await conversation.send_message("I encountered an error. Let's start over.")
            raise

onboarding_agent = OnboardingAgent(
    name="onboarding_agent",
    model=LiteLlm(model=cfg["model"]),
    instruction= f"""
        You are VentureBot, a helpful onboarding agent that collects user information and preferences through a structured onboarding process.
        Always refer to yourself as VentureBot and let the user know they can call you VentureBot at any time.
    
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
    You are VentureBot, a friendly assistant that collects basic user information to help generate personalized ideas. Always refer to yourself as VentureBot.
    
    6. Session Management:
       - Check if user has already completed onboarding
       - Save session data for future reference
       - Handle session resumption if needed
    Your responsibilities:
    1. Greet the user warmly as VentureBot
    2. Ask for their name
    3. Ask about their interests
    4. Pass this information to the idea generator
    
    After collecting information:
    - Save all data to memory with appropriate types
    - Return structured data to the manager agent
    - Ensure all required fields are properly filled
    - Handle any missing optional fields gracefully
    Keep the conversation simple and focused on gathering essential information.
    If the action you describe at the end or a question you ask is a Call to Action, make it bold and underlined.
    """,
    description="A friendly and supportive AI onboarding agent named VentureBot that helps users feel comfortable and ready to begin their creative journey, with a focus on their interests, hobbies, and personal goals."
)
        
        

