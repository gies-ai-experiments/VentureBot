import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator_agent import OrchestratorAgent
from agents.idea_coach_agent import create_idea_coach
from agents.validation_agent import ValidationAgent

# Create mock agents for testing
class MockAgent:
    def __init__(self, name):
        self.name = name
    
    def process(self, payload):
        return f"Processed by {self.name}: {payload}"
    
    def generate_ideas(self, problem_statement):
        return [{"id": 1, "idea": f"Mock idea for: {problem_statement}"}]
    
    def score_ideas(self, ideas):
        return [{"id": idea["id"], "impact": 8.5, "feasibility": 7.0, "innovation": 9.0} for idea in ideas]
    
    def build_prd(self, selected_idea):
        return {"title": f"PRD for idea {selected_idea['id']}", "content": "Mock PRD content"}
    
    def optimize_prompt(self, prompt):
        return f"Optimized: {prompt}"
    
    def coach_pitch(self, pitch):
        return f"Improved pitch: {pitch}"

# Create mock instances of the specialist agents
idea_coach = MockAgent("IdeaCoach")
validation_agent = MockAgent("ValidationAgent")
product_manager_agent = MockAgent("ProductManager")
prompt_engineering_agent = MockAgent("PromptEngineering")
pitch_coach_agent = MockAgent("PitchCoach")

# Create an instance of the OrchestratorAgent
orchestrator = OrchestratorAgent(
    idea_coach_agent=idea_coach,
    validation_agent=validation_agent,
    product_manager_agent=product_manager_agent,
    prompt_engineering_agent=prompt_engineering_agent,
    pitch_coach_agent=pitch_coach_agent
)

print("OrchestratorAgent imported and instantiated successfully!")

# Test message handling with a simple user input for idea generation
test_message_idea = {
    "thread_id": "test-thread-1",
    "user_input": "Generate some ideas for a mobile app"
}

print("\nTesting idea generation intent:")
try:
    response = orchestrator.handle_message(test_message_idea)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test message handling with validation intent
test_message_validate = {
    "thread_id": "test-thread-2",
    "user_input": "Please validate and score these ideas for me"
}

print("\nTesting validation intent:")
try:
    response = orchestrator.handle_message(test_message_validate)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {str(e)}")

# First generate some ideas and cache them
print("\nGenerating ideas to cache:")
orchestrator.handle_message({
    "thread_id": "test-thread-3",
    "user_input": "Generate ideas for a smart home device"
})

# Then test idea selection
test_message_select = {
    "thread_id": "test-thread-3",
    "select_idea": 1
}

print("\nTesting idea selection:")
try:
    response = orchestrator.handle_message(test_message_select)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {str(e)}")