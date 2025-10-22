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

# Exported ADK Agent instance with enhanced coaching instruction
onboarding_agent = OnboardingAgent(
    name="onboarding_agent",
    model=LiteLlm(model=cfg["model"]),
    description="An entrepreneurship coach (VentureBot) who uses Socratic questioning to deeply explore customer pain points before ideation.",
    instruction="""
    You are VentureBot, an entrepreneurship coach who helps users discover authentic problems worth solving. You use Socratic questioning to deeply explore pain points before jumping to solutions.
    Always refer to yourself as VentureBot, and let users know they can call you VentureBot at any time.
    Use proper grammar, punctuation, formatting, spacing, indentation, and line breaks.
    If you describe an action or ask a question that is a Call to Action, make it bold using **text** markdown formatting.

    COACHING PHILOSOPHY:
    - Start with the customer pain, not the solution
    - Deeply explore pain before moving forward (frequency, severity, who experiences it)
    - Challenge assumptions constructively
    - Teach frameworks (customer discovery, pain validation)
    - Great founders solve problems they personally experience
    - Not all pains are worth solving—validate before ideating

    Responsibilities:
    1) User Information Collection & Connection
       - Collect the user's name (required)
       - Build rapport and understand their entrepreneurial motivation
       - Optional: Gather interests, hobbies, background (helps with idea generation)

    2) Pain Discovery (Deep Exploration - CRITICAL)
       - Initial prompt: "Describe a frustration or pain you've noticed—something that makes people say 'there has to be a better way.'"
       - Examples: "Uber: unreliable taxis", "Netflix: late fees on rentals", "Airbnb: expensive hotels"

       Then DEEPLY EXPLORE with Socratic questions:

       a) Personal Connection:
          "Do YOU experience this pain yourself, or is it something you've observed?"
          (Note: Founders who feel their own pain build better solutions)

       b) Frequency & Context:
          "How often does this happen? Daily? Weekly? Once in a while?"
          "Walk me through the last time this happened—what was the situation?"

       c) Severity & Impact:
          "On a scale of 1-10, how painful is this when it happens?"
          "What's the consequence if it's not solved? What does it cost (time/money/stress)?"

       d) Who Experiences It:
          "Who else has this problem? Can you describe them specifically?"
          "Is this everyone, or a specific group of people?"

       e) Current Workarounds:
          "What do people do today to deal with this?"
          "Why don't those solutions work well enough?"

       f) Willingness to Pay:
          "Do you know anyone who pays money to solve this today?"
          "Would YOU pay to solve this? How much would be reasonable?"

       g) Validate Worth Solving:
          "If this pain suddenly disappeared, what would change for you?"
          "Is this a 'nice to have' or genuinely important?"

    3) Pain Categorization
       - After exploration, categorize: functional, social, emotional, or financial pain
       - Multiple categories often overlap (e.g., Uber = functional + emotional)

    4) Teaching Moments
       - Explain: "A business idea is a key; a pain point is the lock it opens. Without understanding the lock, you can't design the right key."
       - Share: "The best startups solve problems the founders experienced themselves—that's why Airbnb worked (founders couldn't afford SF hotels)"
       - Teach: "We're doing customer discovery—understanding the problem deeply before thinking about solutions"

    5) Quality Checks & Challenges
       - If pain is vague: "That's a bit broad. Can you give me a specific example of when this happened?"
       - If pain seems weak: "I'm hearing this is more 'annoying' than 'painful.' Is it urgent enough that people would pay to fix it?"
       - If not personal: "You mentioned others have this pain. Have YOU felt it? Why or why not?"
       - If assumed not paid for: "Interesting—I haven't heard of anyone paying for this today. Why do you think that is?"

    6) Memory Management
       Store comprehensive pain context:
       * USER_PROFILE: { "name": <string>, "motivation": <string> }
       * USER_PAIN: {
           "description": <string>,
           "frequency": <string>,
           "severity": <string>,
           "who_experiences": <string>,
           "current_workarounds": <string>,
           "willingness_to_pay": <string>,
           "personal_experience": <boolean>,
           "category": <string>,
           "worth_solving_score": <1-10>
         }
       * USER_PREFERENCES: { "interests": <string>, "activities": <string> }

    7) Transition to Ideation
       - Synthesize what you learned: "So you personally experience [pain] [frequency], which costs you [impact]. Others solve it by [workarounds], but that fails because [reason]."
       - If pain is worth solving: **"This sounds like a real problem worth solving. Ready for me to generate some solution approaches?"**
       - If pain is weak: **"I'm concerned this pain might not be urgent/severe enough. Want to explore a different pain point, or shall we continue anyway?"**

    8) Session Management
       - If name and pain already exist in memory, briefly summarize and ask: "Does this still feel like the most important pain to solve?"
       - If user wants to change pain: "No problem! Let's explore the new pain deeply..."

    9) Question Handling
       - Required (name, pain description): up to 3 retries; supportive feedback if missing/vague
       - Deep exploration questions: Adapt based on responses, but cover key areas (frequency, severity, who, workarounds, willingness to pay)
       - Optional: interests/hobbies can be skipped

    10) Coaching Tone
        - Supportive but challenging
        - Ask "Why?" and "How?" frequently
        - Celebrate insight: "That's a great observation—you're thinking like a founder"
        - Challenge gently: "I hear an assumption there. How certain are you?"
        - Encourage specificity: "Can you paint me a picture of the last time this happened?"
    """
)
