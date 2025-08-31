import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent

from manager.tools.tools import claude_web_search
from manager.tools.market_analyzer import MarketAnalyzer
from manager.tools.dashboard_generator import DashboardGenerator

dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)  # loads ANTHROPIC_API_KEY from .env
# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to the VentureBots directory and get config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "config.yaml")
cfg = yaml.safe_load(open(config_path))

# Create Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ClaudeWebSearchValidator(Agent):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize after parent class to avoid Pydantic field validation
        object.__setattr__(self, 'market_analyzer', MarketAnalyzer())
        object.__setattr__(self, 'dashboard_generator', DashboardGenerator())
    """
    Validator agent that uses Claude's web search capability to evaluate ideas.
    Scores ideas based on feasibility and innovation using web search results.
    """
    async def handle(self, conversation, memory):
        import time
        import asyncio
        
        try:
            print("Starting idea validation")
            selected_idea = memory.get("SelectedIdea")  # single {"id", "idea"}
            if not selected_idea:
                await conversation.send_message("No idea selected for validation. Please select an idea first.")
                return []
            
            print(f"Validating selected idea: {selected_idea['idea']}")
            
            # Send initial message to user
            await conversation.send_message(f"🔍 **Validating your idea:** {selected_idea['idea']}\n\n🌐 Searching the web for market information, competitors, and similar products...")
            
            # Use real web search function with comprehensive timeout protection
            try:
                print("Starting real web search validation...")
                start_time = time.time()
                
                # Add timeout protection (max 35 seconds for web search)
                search_results = claude_web_search(selected_idea["idea"], anthropic_client)
                try:
                    search_results = await asyncio.wait_for(search_task, timeout=35.0)
                    num_results = len(search_results.get("results", []))
                    print(f"Web search completed in {time.time() - start_time:.2f}s, found {num_results} real market results")
                    
                    # Send progress update to user
                    await conversation.send_message(f"✅ Found {num_results} market findings. Analyzing competitive landscape...")
                    
                except asyncio.TimeoutError:
                    print("Web search timeout - using fallback scoring")
                    search_results = {"results": [], "analysis_type": "timeout"}
                    await conversation.send_message("⚠️ Web search taking longer than expected. Using alternative analysis methods...")
                    
            except Exception as search_error:
                print(f"Web search failed: {search_error}")
                # Fallback to default scoring if web search fails completely
                search_results = {"results": [], "analysis_type": "error"}
                await conversation.send_message("⚠️ Web search temporarily unavailable. Using alternative market analysis...")
            
            # Use advanced market analysis system
            try:
                print("Running comprehensive market analysis...")
                market_scores, market_intelligence = self.market_analyzer.analyze_market_intelligence(search_results)
                
                # Generate rich visual dashboard
                dashboard = self.dashboard_generator.generate_comprehensive_dashboard(
                    selected_idea['idea'], 
                    market_scores, 
                    market_intelligence
                )
                
                print(f"Advanced analysis completed - Overall score: {market_scores.overall_score:.2f}")
                
                # Create backwards-compatible score for memory storage
                score = {
                    "id": selected_idea.get("id", 1),
                    "feasibility": market_scores.execution_feasibility,
                    "innovation": market_scores.innovation_potential,
                    "score": market_scores.overall_score,
                    "notes": f"Advanced market analysis - Confidence: {market_scores.confidence:.2f}",
                    "market_scores": market_scores,
                    "market_intelligence": market_intelligence
                }
                
                # Store enhanced validation results in memory
                memory["Validator"] = score
                
                # Send comprehensive dashboard to user
                await conversation.send_message(dashboard)
                return [score]
                
            except Exception as analysis_error:
                print(f"Advanced analysis failed, falling back to basic scoring: {analysis_error}")
                
                # Fallback to basic scoring if advanced analysis fails
                num_results = len(search_results.get("results", []))
                feasibility = min(num_results/8, 1.0)  # Better scaling for feasibility
                innovation = max(1.0 - num_results/12, 0.0)  # Better scaling for innovation
                final_score = feasibility * 0.6 + innovation * 0.4
            
            # Generate more detailed analysis based on result count
            if num_results <= 3:
                analysis_note = "High innovation potential with limited market competition detected."
            elif num_results <= 6:
                analysis_note = "Good balance of market opportunity and feasibility indicators."
            elif num_results <= 10:
                analysis_note = "Established market with good feasibility but moderate innovation potential."
            else:
                analysis_note = "Highly competitive market - consider unique differentiation strategies."
            
            score = {
                "id": selected_idea.get("id", 1),
                "feasibility": round(feasibility, 2),
                "innovation": round(innovation, 2),
                "score": round(final_score, 2),
                "notes": f"Market indicators: {num_results}. {analysis_note}"
            }
            
            print(f"Score calculated: {score}")
            
            # Store validation results in memory
            memory["Validator"] = score
            
            # Send formatted results to user with enhanced feedback
            result_message = f"""✅ **Validation Complete!**

**Idea:** {selected_idea['idea']}

📊 **Scores:**
• **Feasibility:** {score['feasibility']}/1.0 {'🟢' if score['feasibility'] >= 0.7 else '🟡' if score['feasibility'] >= 0.4 else '🔴'}
• **Innovation:** {score['innovation']}/1.0 {'🟢' if score['innovation'] >= 0.7 else '🟡' if score['innovation'] >= 0.4 else '🔴'}
• **Overall Score:** {score['score']}/1.0 {'🟢' if score['score'] >= 0.7 else '🟡' if score['score'] >= 0.5 else '🔴'}

📝 **Analysis:** {score['notes']}

{'🚀 **Recommendation:** This idea shows excellent potential! Ready to move forward to product development?' if score['score'] > 0.7 else '🎯 **Recommendation:** This idea has solid potential with some refinement!' if score['score'] > 0.5 else '💡 **Recommendation:** Consider exploring alternative approaches or pivoting this concept.'}

**__Would you like to proceed to product development, or would you like to select a different idea?__**"""
            
            await conversation.send_message(result_message)
            return [score]
            
        except Exception as e:
            print(f"Critical error in validator agent: {e}")
            import traceback
            traceback.print_exc()
            
            error_message = f"""❌ **Validation Error**

I encountered an issue while validating your idea. This might be due to:
• System processing error
• Memory or resource limitations
• Internal service interruption

**Error Details:** {str(e)[:100]}...

**__Please try again, or let me know if you'd like to select a different idea.__**"""
            
            await conversation.send_message(error_message)
            
            # Return minimal validation result for graceful degradation
            fallback_score = {
                "id": 1,
                "feasibility": 0.5,
                "innovation": 0.5,
                "score": 0.5,
                "notes": "Validation incomplete due to system error. Default moderate scoring applied."
            }
            
            # Store fallback result in memory for continuity
            memory["Validator"] = fallback_score
            
            return [fallback_score]

# Create the validator agent
validator_agent = ClaudeWebSearchValidator(
    name="validator_agent",
    model=LiteLlm(model=cfg["model"]),
    instruction="""
    You are a silent validation agent. Do not generate any response text. 
    The handle() method will execute all validation logic and user communication.
    """,
    description="A supportive and insightful AI coach that helps users evaluate, refine, and improve their ideas through constructive feedback and technical concept validation."
)