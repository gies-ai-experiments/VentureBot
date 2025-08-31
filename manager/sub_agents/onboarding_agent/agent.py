import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent
import logging
import asyncio
from typing import ClassVar

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
load_dotenv(dotenv_path) # loads ANTHROPIC_API_KEY from .env
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

    async def _ask_required(self, conversation, prompt: str, retry_hint: str) -> str:
        """Ask a required question with retries + timeout."""
        for attempt in range(self.MAX_RETRIES):
            try:
                await conversation.send_message(prompt)
                resp = await asyncio.wait_for(conversation.receive_message(), timeout=self.TIMEOUT)
                if resp and resp.strip().lower() not in {"skip", ""}:
                    return resp.strip()
                await conversation.send_message(retry_hint)
            except asyncio.TimeoutError:
                logger.warning("Timeout on required question attempt %d", attempt + 1)
                if attempt < self.MAX_RETRIES - 1:
                    await conversation.send_message("I didn’t receive a response. Let’s try once more.")
        # Final fallback (keep flow moving; manager can loop back later)
        return "Not specified"

    async def _ask_optional(self, conversation, prompt: str) -> str:
        """Ask an optional question; allow 'skip' and handle timeout gracefully."""
        try:
            await conversation.send_message(prompt + " (type 'skip' to skip)")
            resp = await asyncio.wait_for(conversation.receive_message(), timeout=self.TIMEOUT)
            if not resp:
                return ""
            if resp.strip().lower() == "skip":
                return ""
            return resp.strip()
        except asyncio.TimeoutError:
            logger.info("Optional question timeout; skipping.")
            return ""

    async def handle(self, conversation, memory):
        try:
            logger.info("Starting onboarding process")

            # Session resumption: if already onboarded (name + pain), short confirm & exit
            existing_name = memory.get("USER_PROFILE", {}).get("name") if isinstance(memory.get("USER_PROFILE"), dict) else None
            existing_pain = memory.get("USER_PAIN", {}).get("description") if isinstance(memory.get("USER_PAIN"), dict) else None
            if existing_name and existing_pain:
                await conversation.send_message(
                    f"Hi {existing_name}! I’ve got your pain point saved: “{existing_pain}”. "
                    "**Would you like me to generate a few ideas now?**"
                )
                return {
                    "USER_PROFILE": memory.get("USER_PROFILE"),
                    "USER_PAIN": memory.get("USER_PAIN"),
                    "USER_PREFERENCES": memory.get("USER_PREFERENCES", {})
                }

            # Warm, concise intro with “key & lock” metaphor
            await conversation.send_message(
                "I’m **VentureBot**. Great products start with real problems. "
                "Think of the **idea** as a _key_ and the **pain point** as the _lock_ it opens. "
                "We’ll capture your details, then I’ll generate ideas tailored to your pain.\n\n"
                "We’ll do: your **name → pain point → (optional) interests/activities**. "
                "You can type **skip** on optional parts."
            )

            # Required: name
            name = await self._ask_required(
                conversation,
                "What’s your **name**?",
                "Thanks—please share your **name** so I can personalize things."
            )

            # Required: pain (with examples + category)
            pain_prompt = (
                "Briefly describe a **frustration/pain** you’ve noticed (1–2 lines). "
                "Examples: *waiting too long for deliveries*, *confusing forms*, *expensive subscriptions*, *team info scattered in chats*."
            )
            pain = await self._ask_required(
                conversation,
                pain_prompt,
                "A concrete pain helps me generate better solutions. One sentence about the problem is perfect."
            )

            # Optional: categorize pain
            pain_cat = await self._ask_optional(
                conversation,
                "What **type** of pain is this? (functional / social / emotional / financial)"
            )
            if pain_cat:
                pain_cat = pain_cat.lower()

            # Optional: interests/hobbies/activities
            interests = await self._ask_optional(conversation, "Any **interests or hobbies** you want me to factor in?")
            activities = await self._ask_optional(conversation, "Any **favorite activities** or topics that excite you?")

            # Persist memory using new schema
            profile_blob = {"name": name} if name else {}
            pain_blob = {"description": pain, "category": pain_cat or ""}
            prefs_blob = {
                "interests": interests or "",
                "activities": activities or ""
            }

            memory["USER_PROFILE"] = profile_blob               # name
            memory["USER_PAIN"] = pain_blob                     # pain description + category
            memory["USER_PREFERENCES"] = prefs_blob             # interests, activities

            # Positive reinforcement + hand-off CTA
            await conversation.send_message(
                f"Great insight, {profile_blob.get('name', 'there')}—that’s exactly the kind of pain successful founders solve.\n\n"
                "**Excellent! Next I’ll generate five idea keys to fit the lock you described—ready?**"
            )

            # Return structured data to manager for next agent
            return {
                "USER_PROFILE": profile_blob,
                "USER_PAIN": pain_blob,
                "USER_PREFERENCES": prefs_blob
            }

        except Exception as e:
            logger.error(f"Error in onboarding process: {e}")
            await conversation.send_message("I hit a snag. Let’s restart onboarding from the top.")
            raise

# Exported ADK Agent instance with new concise instruction
onboarding_agent = OnboardingAgent(
    name="onboarding_agent",
    model=LiteLlm(model=cfg["model"]),
    description="A warm, motivational onboarding agent (VentureBot) that anchors onboarding in real pain points, interests, and goals.",
    instruction="""
    You are VentureBot, a supportive onboarding agent who helps users begin their creative journey by focusing on real customer pain points and personal motivation.
    Always refer to yourself as VentureBot, and let users know they can call you VentureBot at any time.
    Use proper grammar, punctuation, formatting, spacing, indentation, and line breaks.
    If you describe an action or ask a question that is a Call to Action, make it bold using **text** markdown formatting.

    Responsibilities:
    1) User Information Collection
       - Collect the user's name (required)
       - Guide the user to describe a frustration, pain point, or problem they've noticed (required; offer examples: “waiting too long for deliveries”, “confusing forms”, “expensive subscriptions”)
       - Gather interests or hobbies (optional)
       - Understand favorite activities or what excites them (optional)

    2) Framing & Motivation
       - Explain: “A business idea is a key; a pain point is the lock it opens.”
       - Mini-timeline: learn about you → capture pain → generate ideas → you pick a favorite
       - Examples of pain-driven innovations (Uber vs unreliable taxis, Netflix vs late fees)
       - Ask: “Is your pain functional, social, emotional, or financial?”
       - Remind: optional questions can be skipped; users can type “add pain” later to revisit

    3) Question Handling
       - Required (name, pain): up to 3 retries; 5 minutes timeout; supportive feedback if missing/vague
       - Optional: allow 'skip'; 5 minutes; gracefully handle timeouts

    4) Error Handling
       - Handle timeouts gracefully
       - Provide friendly, encouraging error messages
       - Maintain conversation flow after errors

    5) Memory Management
       - Store:
         * USER_PROFILE: { "name": <string> }
         * USER_PAIN:    { "description": <string>, "category": <string> }
         * USER_PREFERENCES: { "interests": <string>, "activities": <string> }
       - Ensure persistence across the session

    6) User Experience
       - Celebrate each response (“Great insight! That’s exactly the kind of pain successful founders tackle.”)
       - End with: **“Excellent! Next I’ll generate five idea keys to fit the lock you described—ready?”**

    7) Session Management
       - If name and pain already exist in memory, confirm and offer to move ahead to idea generation
    """
)
