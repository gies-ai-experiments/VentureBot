#!/usr/bin/env python3
"""
Unit tests for the validator agent and web search functionality.
Tests the core validation logic, error handling, and circuit breaker patterns.
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from manager.tools.tools import claude_web_search, validation_circuit_breaker, ValidationCircuitBreaker
from manager.sub_agents.validator_agent.agent import ClaudeWebSearchValidator


class TestValidationCircuitBreaker(unittest.TestCase):
    """Test the circuit breaker functionality"""
    
    def setUp(self):
        """Reset circuit breaker before each test"""
        self.circuit_breaker = ValidationCircuitBreaker(failure_threshold=3, recovery_timeout=60)
    
    def test_initial_state(self):
        """Test circuit breaker initial state"""
        self.assertTrue(self.circuit_breaker.can_proceed())
        self.assertFalse(self.circuit_breaker.is_open)
        self.assertEqual(self.circuit_breaker.failure_count, 0)
    
    def test_success_recording(self):
        """Test recording successful operations"""
        self.circuit_breaker.record_success()
        self.assertTrue(self.circuit_breaker.can_proceed())
        self.assertFalse(self.circuit_breaker.is_open)
        self.assertEqual(self.circuit_breaker.failure_count, 0)
    
    def test_failure_recording(self):
        """Test recording failed operations"""
        # Record failures below threshold
        self.circuit_breaker.record_failure()
        self.assertTrue(self.circuit_breaker.can_proceed())
        self.assertEqual(self.circuit_breaker.failure_count, 1)
        
        self.circuit_breaker.record_failure()
        self.assertTrue(self.circuit_breaker.can_proceed())
        self.assertEqual(self.circuit_breaker.failure_count, 2)
        
        # Record failure that triggers circuit breaker
        self.circuit_breaker.record_failure()
        self.assertFalse(self.circuit_breaker.can_proceed())
        self.assertTrue(self.circuit_breaker.is_open)
        self.assertEqual(self.circuit_breaker.failure_count, 3)
    
    def test_circuit_reset(self):
        """Test manual circuit breaker reset"""
        # Trigger circuit breaker
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        self.assertFalse(self.circuit_breaker.can_proceed())
        
        # Reset circuit breaker
        self.circuit_breaker.reset()
        self.assertTrue(self.circuit_breaker.can_proceed())
        self.assertFalse(self.circuit_breaker.is_open)
        self.assertEqual(self.circuit_breaker.failure_count, 0)


class TestClaudeWebSearch(unittest.TestCase):
    """Test the mock web search functionality"""
    
    def setUp(self):
        """Reset circuit breaker before each test"""
        validation_circuit_breaker.reset()
    
    def test_basic_search(self):
        """Test basic web search functionality"""
        result = claude_web_search("social media app")
        
        self.assertIn("results", result)
        self.assertIsInstance(result["results"], list)
        self.assertGreater(len(result["results"]), 0)
        
        # Check result structure
        first_result = result["results"][0]
        self.assertIn("title", first_result)
        self.assertIn("content", first_result)
        self.assertIn("position", first_result)
    
    def test_saturation_scoring(self):
        """Test scoring based on market saturation keywords"""
        # Test highly saturated market
        saturated_result = claude_web_search("social media messaging chat app")
        saturated_count = len(saturated_result["results"])
        
        # Test innovative idea
        innovative_result = claude_web_search("ai machine learning blockchain optimization")
        innovative_count = len(innovative_result["results"])
        
        # Saturated markets should have more results than innovative ones
        self.assertGreater(saturated_count, innovative_count)
    
    def test_innovation_scoring(self):
        """Test scoring based on innovation keywords"""
        # Test basic idea
        basic_result = claude_web_search("simple calculator app")
        basic_count = len(basic_result["results"])
        
        # Test AI-powered idea
        ai_result = claude_web_search("ai-powered personalization recommendation engine")
        ai_count = len(ai_result["results"])
        
        # AI ideas should have fewer results (more innovative)
        self.assertLessEqual(ai_count, basic_count)
    
    def test_empty_query_handling(self):
        """Test handling of empty or invalid queries"""
        # Test empty string
        result = claude_web_search("")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)  # Should return fallback
        
        # Test None query
        result = claude_web_search(None)
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)  # Should return fallback
    
    def test_circuit_breaker_integration(self):
        """Test web search with circuit breaker"""
        # Trigger circuit breaker
        for _ in range(3):
            validation_circuit_breaker.record_failure()
        
        # Search should return fallback when circuit is open
        result = claude_web_search("test query")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertIn("circuit breaker", result["results"][0]["content"].lower())
    
    def test_result_count_range(self):
        """Test that result count stays within expected range"""
        test_queries = [
            "basic app",
            "social media facebook instagram",
            "ai machine learning blockchain",
            "enterprise real-time distributed system"
        ]
        
        for query in test_queries:
            result = claude_web_search(query)
            result_count = len(result["results"])
            
            # Should be between 1 and 15 results
            self.assertGreaterEqual(result_count, 1)
            self.assertLessEqual(result_count, 15)


class TestValidatorAgent(unittest.TestCase):
    """Test the validator agent functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.validator = ClaudeWebSearchValidator(name="test_validator")
        self.mock_conversation = Mock()
        self.mock_conversation.send_message = AsyncMock()
        
        # Reset circuit breaker
        validation_circuit_breaker.reset()
    
    async def test_basic_validation(self):
        """Test basic idea validation"""
        memory = {
            "SelectedIdea": {
                "id": 1,
                "idea": "AI-powered fitness tracking app"
            }
        }
        
        result = await self.validator.handle(self.mock_conversation, memory)
        
        # Should return validation results
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        score = result[0]
        self.assertIn("id", score)
        self.assertIn("feasibility", score)
        self.assertIn("innovation", score)
        self.assertIn("score", score)
        self.assertIn("notes", score)
        
        # Scores should be between 0 and 1
        self.assertGreaterEqual(score["feasibility"], 0)
        self.assertLessEqual(score["feasibility"], 1)
        self.assertGreaterEqual(score["innovation"], 0)
        self.assertLessEqual(score["innovation"], 1)
        self.assertGreaterEqual(score["score"], 0)
        self.assertLessEqual(score["score"], 1)
        
        # Should store result in memory
        self.assertIn("Validator", memory)
        
        # Should send messages to user
        self.assertTrue(self.mock_conversation.send_message.called)
        calls = self.mock_conversation.send_message.call_args_list
        self.assertGreater(len(calls), 1)  # Should send initial message and results
    
    async def test_missing_selected_idea(self):
        """Test handling when no idea is selected"""
        memory = {}
        
        result = await self.validator.handle(self.mock_conversation, memory)
        
        # Should return empty result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        
        # Should send error message
        self.assertTrue(self.mock_conversation.send_message.called)
        message = self.mock_conversation.send_message.call_args[0][0]
        self.assertIn("No idea selected", message)
    
    async def test_validation_scoring_algorithm(self):
        """Test the validation scoring algorithm"""
        test_cases = [
            {
                "idea": "social media chat app",
                "expected_feasibility": "high",  # saturated market = high feasibility
                "expected_innovation": "low"     # saturated market = low innovation
            },
            {
                "idea": "ai machine learning optimization",
                "expected_feasibility": "medium", # moderate complexity
                "expected_innovation": "high"     # innovative keywords
            }
        ]
        
        for case in test_cases:
            memory = {
                "SelectedIdea": {
                    "id": 1,
                    "idea": case["idea"]
                }
            }
            
            result = await self.validator.handle(self.mock_conversation, memory)
            score = result[0]
            
            if case["expected_feasibility"] == "high":
                self.assertGreater(score["feasibility"], 0.6)
            elif case["expected_feasibility"] == "low":
                self.assertLess(score["feasibility"], 0.4)
            
            if case["expected_innovation"] == "high":
                self.assertGreater(score["innovation"], 0.6)
            elif case["expected_innovation"] == "low":
                self.assertLess(score["innovation"], 0.4)
    
    @patch('manager.sub_agents.validator_agent.agent.claude_web_search')
    async def test_error_handling(self, mock_search):
        """Test error handling in validator agent"""
        # Mock search failure
        mock_search.side_effect = Exception("Test error")
        
        memory = {
            "SelectedIdea": {
                "id": 1,
                "idea": "test idea"
            }
        }
        
        result = await self.validator.handle(self.mock_conversation, memory)
        
        # Should return fallback result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        score = result[0]
        self.assertEqual(score["feasibility"], 0.5)
        self.assertEqual(score["innovation"], 0.5)
        self.assertEqual(score["score"], 0.5)
        
        # Should store fallback in memory
        self.assertEqual(memory["Validator"], score)
        
        # Should send error message
        self.assertTrue(self.mock_conversation.send_message.called)
        error_message = self.mock_conversation.send_message.call_args_list[-1][0][0]
        self.assertIn("Validation Error", error_message)


def run_async_test(test_func):
    """Helper to run async test functions"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func())
    finally:
        loop.close()


# Convert async test methods to sync for unittest
def add_async_tests():
    """Add async test methods to TestValidatorAgent"""
    async_methods = [
        'test_basic_validation',
        'test_missing_selected_idea', 
        'test_validation_scoring_algorithm',
        'test_error_handling'
    ]
    
    for method_name in async_methods:
        async_method = getattr(TestValidatorAgent, method_name)
        
        def make_sync_test(async_func):
            def sync_test(self):
                return run_async_test(lambda: async_func(self))
            return sync_test
        
        setattr(TestValidatorAgent, method_name, make_sync_test(async_method))


# Apply async test conversion
add_async_tests()


if __name__ == "__main__":
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Running VentureBot Validator Agent Tests")
    print("=" * 50)
    
    # Run tests
    unittest.main(verbosity=2)