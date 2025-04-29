from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext
from typing import AsyncGenerator, List, Dict, Optional, Any, Union
import logging
import time
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.ads_utils import get_google_ads_metrics, safe_rate_text, extract_nouns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def rate_text(text: str, criterion: str) -> Optional[float]:
    """
    Stub function to rate text based on a specific criterion.
    
    Args:
        text: The text to rate
        criterion: The criterion to rate against (impact, feasibility, innovation)
        
    Returns:
        A score between 0 and 10, or None if rating fails
    """
    # This is a stub implementation - in production, this would call an actual rating service
    # For now, return a simple score based on text length and criterion
    try:
        # Simulate potential failures
        if not text or not criterion:
            return None
            
        # Simple scoring logic for demonstration
        if criterion == "impact":
            return min(len(text) / 20, 10)  # Higher score for longer text, max 10
        elif criterion == "feasibility":
            return min(10, max(0, 10 - len(text) / 30))  # Lower score for longer text
        elif criterion == "innovation":
            return min(8, max(2, len(text) % 10))  # Score between 2-8 based on text length
        else:
            return 5.0  # Default score for unknown criteria
    except Exception:
        # Return None on any error
        return None

class ValidationAgent(BaseAgent):
    """
    1) Reads state['ideas']: List[{"id":int,"idea":str}]
    2) Computes impact/feasibility/innovation via safe_rate_text()
    3) Fetches Google Ads metrics via get_google_ads_metrics()
    4) Normalizes into a google_score 0–10
    5) Writes state['validation_results'] and emits it
    
    Also provides a standalone score_ideas method for direct scoring of ideas
    without Google Ads metrics.
    """
    
    def score_ideas(self, ideas: List[Dict]) -> List[Dict]:
        """
        Score a list of ideas based on impact, feasibility, and innovation.
        
        Args:
            ideas: A list of dictionaries, each with 'id' and 'idea' keys
            
        Returns:
            A list of dictionaries with 'id', 'impact', 'feasibility', and 'innovation' keys
            
        Raises:
            ValueError: If ideas is empty or not a list
        """
        # Validate input
        if not ideas or not isinstance(ideas, list):
            logger.error(f"Invalid ideas input: {ideas}")
            raise ValueError('no ideas to validate')
            
        logger.info(f"Scoring {len(ideas)} ideas with total input length: {sum(len(str(idea.get('idea', ''))) for idea in ideas)} characters")
        
        results = []
        errors = []
        
        # Process each idea
        for idea in ideas:
            start_time = time.time()
            
            try:
                # Validate idea structure
                if 'id' not in idea or 'idea' not in idea:
                    logger.warning(f"Skipping idea with missing fields: {idea}")
                    continue
                
                idea_id = idea['id']
                idea_text = idea['idea']
                
                # Calculate scores
                scores = {}
                for criterion in ['impact', 'feasibility', 'innovation']:
                    try:
                        score = rate_text(idea_text, criterion)
                        
                        # Handle None or error cases
                        if score is None:
                            logger.warning(f"Default score 0 used for idea {idea_id}, criterion {criterion} due to rate_text returning None")
                            score = 0
                            
                        # Clamp score to valid range [0, 10]
                        score = min(10, max(0, score))
                        scores[criterion] = score
                        
                    except Exception as e:
                        logger.warning(f"Default score 0 used for idea {idea_id}, criterion {criterion} due to error: {str(e)}")
                        scores[criterion] = 0
                
                # Add to results
                results.append({
                    "id": idea_id,
                    "impact": scores['impact'],
                    "feasibility": scores['feasibility'],
                    "innovation": scores['innovation']
                })
                
                logger.info(f"Scored idea {idea_id} in {time.time() - start_time:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Error processing idea: {str(e)}")
                errors.append({
                    "idea_id": idea.get('id', 'unknown'),
                    "error": str(e)
                })
        
        # Add errors to result if any occurred
        if errors:
            logger.warning(f"Encountered {len(errors)} errors while scoring ideas")
            return results + [{"errors": errors}]
        
        return results
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        ideas = ctx.session.state.get("ideas", [])
        results = []
        for entry in ideas:
            idea_id, text = entry["id"], entry["idea"]
            # textual scores
            impact    = safe_rate_text(text, "impact")
            feasibility = safe_rate_text(text, "feasibility")
            innovation  = safe_rate_text(text, "innovation")
            # Google Ads metrics
            try:
                keywords = extract_nouns(text)[:3]
                ads = get_google_ads_metrics(keywords)
                norm_srch = min(ads["avg_monthly_searches"]/10000, 1.0)
                comp_sc   = 1 - ads["competition"]
                cpc_sc    = 1 - min(ads["avg_cpc"]/5.0, 1.0)
                google_score = round((norm_srch + comp_sc + cpc_sc)/3 * 10, 1)
            except Exception:
                ads = {"avg_monthly_searches": 0, "competition": 1.0, "avg_cpc": 5.0}
                google_score = 0.0

            results.append({
                "id": idea_id,
                "impact": impact,
                "feasibility": feasibility,
                "innovation": innovation,
                **ads,
                "google_score": google_score
            })

        ctx.session.state["validation_results"] = results
        yield Event(author=self.name, content=str(results))
