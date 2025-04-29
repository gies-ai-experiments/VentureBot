from typing import Dict, Any, List, Optional, Union
import logging
import time
import traceback
from threading import Timer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Orchestrator Agent that coordinates between specialist agents.
    
    This agent routes messages to the appropriate specialist agent based on intent
    and manages the flow of information between agents.
    """
    
    def __init__(self, 
                 idea_coach_agent,
                 validation_agent,
                 product_manager_agent,
                 prompt_engineering_agent,
                 pitch_coach_agent):
        """
        Initialize the OrchestratorAgent with specialist agent instances.
        
        Args:
            idea_coach_agent: Agent for generating ideas
            validation_agent: Agent for validating and scoring ideas
            product_manager_agent: Agent for creating product requirement documents
            prompt_engineering_agent: Agent for optimizing prompts
            pitch_coach_agent: Agent for coaching on pitches
        """
        self.agents = {
            "idea": idea_coach_agent,
            "validate": validation_agent,
            "prd": product_manager_agent,
            "prompt_opt": prompt_engineering_agent,
            "pitch": pitch_coach_agent
        }
        
        # Thread-scoped cache for validation results
        self._validation_cache = {}
        
        # Rate limiting
        self._last_call_time = 0
        self._call_count = 0
        
        logger.info("OrchestratorAgent initialized with all specialist agents")
    
    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming messages and route to appropriate specialist agents.
        
        Args:
            message: A dictionary containing either:
                    - "thread_id" and "user_input" for new prompts
                    - "thread_id" and "select_idea" for idea selection
        
        Returns:
            A dictionary with the response from the appropriate agent or an error message
        """
        try:
            # Validate message format
            if not isinstance(message, dict):
                logger.error(f"Invalid message format: {message}")
                return {"error": "invalid_input"}
            
            # Check for required keys
            if "thread_id" not in message:
                logger.error(f"Missing thread_id in message: {message}")
                return {"error": "invalid_input"}
            
            thread_id = message["thread_id"]
            
            # Handle rate limiting
            current_time = time.time()
            if current_time - self._last_call_time < 1:  # Within 1 second window
                self._call_count += 1
                if self._call_count > 3:  # More than 3 calls per second
                    logger.warning(f"Rate limit exceeded for thread {thread_id}, sleeping 1s")
                    time.sleep(1)
                    self._call_count = 1
                    self._last_call_time = time.time()
            else:
                # Reset counter for new time window
                self._call_count = 1
                self._last_call_time = current_time
            
            # Process based on message type
            if "user_input" in message:
                user_input = message["user_input"]
                return self._handle_user_input(thread_id, user_input)
            elif "select_idea" in message:
                idea_id = message["select_idea"]
                return self._handle_idea_selection(thread_id, idea_id)
            else:
                logger.error(f"Message missing required keys: {message}")
                return {"error": "invalid_input"}
                
        except Exception as e:
            # Catch-all exception handler
            logger.error(f"Orchestrator error: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": "orchestrator_error"}
    
    def _handle_user_input(self, thread_id: str, user_input: str) -> Dict[str, Any]:
        """
        Process user input by classifying intent and routing to appropriate agent.
        
        Args:
            thread_id: The ID of the conversation thread
            user_input: The text input from the user
            
        Returns:
            Response from the appropriate agent
        """
        # Classify intent
        intent = self._classify_intent(user_input)
        logger.info(f"Classified intent for thread {thread_id}: {intent}")
        
        # Handle validation intent specially
        if intent == "validate":
            try:
                # Get the last ideas from cache or another source
                # This is a placeholder - in a real implementation, you would retrieve
                # the last ideas from a persistent storage
                last_ideas = self._get_cached_results(thread_id).get("ideas", [])
                
                if not last_ideas:
                    logger.warning(f"No ideas found for validation in thread {thread_id}")
                    return {
                        "thread_id": thread_id,
                        "agent": "Orchestrator",
                        "result": "error",
                        "error": "no_ideas_to_validate"
                    }
                
                # Call validation agent with timeout
                def timeout_handler():
                    raise TimeoutError("ValidationAgent call timed out")
                
                timer = Timer(5, timeout_handler)
                try:
                    timer.start()
                    validation_results = self.agents["validate"].score_ideas(last_ideas)
                finally:
                    timer.cancel()
                
                # Cache the results
                self._cache_validation_results(thread_id, validation_results)
                
                logger.info(f"Validation completed for thread {thread_id}: {len(validation_results)} results")
                
                return {
                    "thread_id": thread_id,
                    "agent": "Orchestrator",
                    "result": "validation_scores",
                    "scores": validation_results
                }
            except TimeoutError:
                logger.error(f"ValidationAgent timed out for thread {thread_id}")
                return {"error": "ValidationAgent_failed"}
            except Exception as e:
                logger.error(f"ValidationAgent failed: {str(e)}")
                logger.error(traceback.format_exc())
                return {"error": "ValidationAgent_failed"}
        
        # Route to appropriate agent for other intents
        return self._route_to_agent(thread_id, intent, user_input)
    
    def _handle_idea_selection(self, thread_id: str, idea_id: int) -> Dict[str, Any]:
        """
        Process idea selection by retrieving validation results and calling ProductManagerAgent.
        
        Args:
            thread_id: The ID of the conversation thread
            idea_id: The ID of the selected idea
            
        Returns:
            Response with the PRD from the ProductManagerAgent
        """
        # Get cached validation results
        validation_results = self._get_cached_results(thread_id)
        
        if not validation_results:
            logger.error(f"No validation results found for thread {thread_id}")
            return {"error": "invalid_selection"}
        
        # Find the selected idea
        selected_idea = None
        
        # Handle different formats of validation_results
        if isinstance(validation_results, dict) and "ideas" in validation_results:
            # Format: {"ideas": [{"id": 1, "idea": "..."}, ...]}
            ideas = validation_results["ideas"]
            for idea in ideas:
                if idea.get("id") == idea_id:
                    selected_idea = idea
                    break
        elif isinstance(validation_results, list):
            # Format: [{"id": 1, ...}, {"id": 2, ...}, ...]
            for result in validation_results:
                if isinstance(result, dict) and result.get("id") == idea_id:
                    selected_idea = result
                    break
        
        logger.info(f"Looking for idea ID {idea_id} in cached results for thread {thread_id}")
        
        if not selected_idea:
            logger.error(f"Invalid idea ID {idea_id} for thread {thread_id}")
            return {"error": "invalid_selection"}
        
        # Call ProductManagerAgent with timeout
        try:
            def timeout_handler():
                raise TimeoutError("ProductManagerAgent call timed out")
            
            timer = Timer(5, timeout_handler)
            try:
                timer.start()
                prd = self.agents["prd"].build_prd(selected_idea)
            finally:
                timer.cancel()
            
            logger.info(f"PRD generated for idea {idea_id} in thread {thread_id}")
            
            return {
                "thread_id": thread_id,
                "agent": "Orchestrator",
                "result": "prd",
                "prd_payload": prd
            }
        except TimeoutError:
            logger.error(f"ProductManagerAgent timed out for thread {thread_id}")
            return {"error": "ProductManagerAgent_failed"}
        except Exception as e:
            logger.error(f"ProductManagerAgent failed: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": "ProductManagerAgent_failed"}
    
    def _classify_intent(self, text: str) -> str:
        """
        Classify the intent of the user input.
        
        Args:
            text: The user input text
            
        Returns:
            One of ["idea", "validate", "prd", "prompt_opt", "pitch"], defaulting to "idea"
        """
        # Simple keyword-based intent classification
        # In a real implementation, this would use a more sophisticated approach
        text_lower = text.lower()
        
        # More specific keyword matching with word boundaries
        validate_keywords = ["validate", "score", "evaluate", "rate", "assessment"]
        idea_keywords = ["generate", "create", "brainstorm", "suggestion", "come up with"]
        
        # Check for validation intent
        if any(f" {keyword} " in f" {text_lower} " for keyword in validate_keywords):
            return "validate"
        # Check for idea generation intent
        elif any(f" {keyword} " in f" {text_lower} " or text_lower.startswith(f"{keyword} ") for keyword in idea_keywords):
            return "idea"
        # Check for the word "idea" but in a generation context
        elif "idea" in text_lower and any(word in text_lower for word in ["new", "some", "more", "generate", "create"]):
            return "idea"
        elif any(keyword in text_lower for keyword in ["prd", "product", "requirement", "document", "spec"]):
            return "prd"
        elif any(keyword in text_lower for keyword in ["prompt", "optimize", "improve", "refine"]):
            return "prompt_opt"
        elif any(keyword in text_lower for keyword in ["pitch", "present", "demo", "showcase"]):
            return "pitch"
        else:
            # Default to idea generation
            return "idea"
    
    def _route_to_agent(self, thread_id: str, intent: str, payload: Any) -> Dict[str, Any]:
        """
        Route the request to the appropriate agent based on intent.
        
        Args:
            thread_id: The ID of the conversation thread
            intent: The classified intent
            payload: The data to send to the agent
            
        Returns:
            Response from the agent
        """
        logger.info(f"Routing intent '{intent}' to agent for thread {thread_id}")
        
        if intent not in self.agents:
            logger.warning(f"Unknown intent '{intent}', defaulting to 'idea' for thread {thread_id}")
            intent = "idea"
        
        agent = self.agents[intent]
        
        # Call agent with timeout
        try:
            def timeout_handler():
                raise TimeoutError(f"{intent} agent call timed out")
            
            timer = Timer(5, timeout_handler)
            try:
                timer.start()
                
                # Call the appropriate method based on intent
                if intent == "idea":
                    result = agent.generate_ideas(payload)
                elif intent == "prompt_opt":
                    result = agent.optimize_prompt(payload)
                elif intent == "pitch":
                    result = agent.coach_pitch(payload)
                else:
                    # Generic fallback
                    result = agent.process(payload)
                
            finally:
                timer.cancel()
            
            logger.info(f"Agent '{intent}' completed processing for thread {thread_id}")
            
            # Cache ideas if generated
            if intent == "idea" and result:
                self._cache_validation_results(thread_id, {"ideas": result})
            
            return {
                "thread_id": thread_id,
                "agent": intent.capitalize(),
                "result": intent,
                "payload": result
            }
            
        except TimeoutError:
            logger.error(f"Agent '{intent}' timed out for thread {thread_id}")
            return {"error": f"{intent}_agent_failed"}
        except Exception as e:
            logger.error(f"Agent '{intent}' failed: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": f"{intent}_agent_failed"}
    
    def _cache_validation_results(self, thread_id: str, results: Dict):
        """
        Cache validation results for a thread.
        
        Args:
            thread_id: The ID of the conversation thread
            results: The validation results to cache
        """
        self._validation_cache[thread_id] = results
        logger.info(f"Cached results for thread {thread_id}")
    
    def _get_cached_results(self, thread_id: str) -> Dict:
        """
        Retrieve cached validation results for a thread.
        
        Args:
            thread_id: The ID of the conversation thread
            
        Returns:
            The cached validation results or an empty dict if none exist
        """
        results = self._validation_cache.get(thread_id, {})
        if results:
            logger.info(f"Retrieved cached results for thread {thread_id}")
        else:
            logger.warning(f"No cached results found for thread {thread_id}")
        return results