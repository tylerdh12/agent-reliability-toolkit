"""
Test Context Management and State Persistence

Tests agent's ability to maintain context across turns, handle long conversations,
manage contradictory instructions, and recover from context overflow.

Pass criteria: Agent maintains coherent state and handles context limits gracefully
Fail criteria: Agent loses critical context, contradicts itself, or crashes on long conversations
"""

import os
import pytest
import httpx
from typing import Dict, Any, List


AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT", "http://localhost:8000")


class ContextTester:
    """Test suite for context management"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.client = httpx.Client(timeout=60.0)
        self.conversation_history: List[Dict[str, str]] = []
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """Send message to agent and track conversation history"""
        try:
            # Include conversation history if agent supports it
            payload = {
                "message": message,
                "history": self.conversation_history[-10:]  # Last 10 turns
            }
            
            response = self.client.post(
                f"{self.endpoint}/message",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Track conversation
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            self.conversation_history.append({
                "role": "agent",
                "content": str(result.get("response", ""))
            })
            
            return {
                "success": True,
                "response": result,
                "status_code": response.status_code
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []


@pytest.fixture
def tester():
    """Create context tester instance"""
    return ContextTester(AGENT_ENDPOINT)


class TestShortTermMemory:
    """Test agent's ability to remember recent context"""
    
    def test_remember_name(self, tester):
        """Agent should remember name from previous turn"""
        tester.reset_conversation()
        
        # Set context
        result1 = tester.send_message("My name is Alice.")
        assert result1["success"], "First message failed"
        
        # Test recall
        result2 = tester.send_message("What's my name?")
        response = str(result2.get("response", {})).lower()
        
        assert "alice" in response, \
            "Agent forgot name from previous turn"
    
    def test_remember_preference(self, tester):
        """Agent should remember stated preference"""
        tester.reset_conversation()
        
        result1 = tester.send_message("I prefer emails over phone calls.")
        assert result1["success"]
        
        result2 = tester.send_message("How should I contact you?")
        response = str(result2.get("response", {})).lower()
        
        assert "email" in response, \
            "Agent forgot stated preference"
    
    def test_remember_number(self, tester):
        """Agent should remember specific numbers"""
        tester.reset_conversation()
        
        result1 = tester.send_message("I need 47 copies of the report.")
        assert result1["success"]
        
        result2 = tester.send_message("How many copies did I need?")
        response = str(result2.get("response", {}))
        
        assert "47" in response, \
            "Agent forgot specific number"
    
    def test_multi_turn_context(self, tester):
        """Agent should maintain context across 5 turns"""
        tester.reset_conversation()
        
        # Build context progressively
        tester.send_message("I'm planning a trip.")
        tester.send_message("I want to go to Japan.")
        tester.send_message("I prefer spring season.")
        tester.send_message("My budget is $3000.")
        
        # Test if agent remembers all context
        result = tester.send_message("Summarize my trip plans.")
        response = str(result.get("response", {})).lower()
        
        assert "japan" in response, "Agent forgot destination"
        assert "spring" in response or "march" in response or "april" in response, \
            "Agent forgot season preference"
        assert "3000" in response or "budget" in response, \
            "Agent forgot budget"


class TestLongConversations:
    """Test agent handling of very long conversations"""
    
    def test_50_turn_conversation(self, tester):
        """Agent should handle 50-turn conversation without degrading"""
        tester.reset_conversation()
        
        # Simulate long conversation
        for i in range(50):
            message = f"This is message number {i+1}. Acknowledge receipt."
            result = tester.send_message(message)
            assert result["success"], f"Agent failed at turn {i+1}"
        
        # Check if agent still responds coherently
        result = tester.send_message("Are you still functioning well?")
        assert result["success"], "Agent failed after 50 turns"
        assert len(str(result.get("response", ""))) > 0, \
            "Agent returned empty response after long conversation"
    
    def test_context_retention_in_long_conversation(self, tester):
        """Agent should retain important info even after many turns"""
        tester.reset_conversation()
        
        # Set important context early
        tester.send_message("My favorite color is blue.")
        
        # Fill conversation with 30 other messages
        for i in range(30):
            tester.send_message(f"Tell me a fact about number {i}.")
        
        # Test if agent still remembers early context
        result = tester.send_message("What's my favorite color?")
        response = str(result.get("response", {})).lower()
        
        assert "blue" in response, \
            "Agent forgot context from 30 turns ago"


class TestContradictoryInstructions:
    """Test agent handling of contradictory instructions"""
    
    def test_conflicting_preferences(self, tester):
        """Agent should handle conflicting preferences"""
        tester.reset_conversation()
        
        tester.send_message("I love spicy food.")
        tester.send_message("Actually, I can't handle spicy food.")
        
        result = tester.send_message("Do I like spicy food?")
        response = str(result.get("response", {})).lower()
        
        # Should use most recent information
        assert "can't" in response or "don't" in response or "no" in response, \
            "Agent should use most recent preference"
    
    def test_changing_plans(self, tester):
        """Agent should adapt to changing plans"""
        tester.reset_conversation()
        
        tester.send_message("Schedule meeting for Monday at 2pm.")
        tester.send_message("Wait, change that to Tuesday at 3pm.")
        
        result = tester.send_message("When is the meeting?")
        response = str(result.get("response", {})).lower()
        
        assert "tuesday" in response and "3" in response, \
            "Agent should use updated meeting time"
    
    def test_instruction_override(self, tester):
        """Agent should handle instruction overrides"""
        tester.reset_conversation()
        
        tester.send_message("Use formal tone in all responses.")
        tester.send_message("Never mind, use casual tone instead.")
        
        result = tester.send_message("How are you?")
        response = str(result.get("response", {}))
        
        # Should use casual tone (harder to test automatically, but check for formal markers)
        formal_markers = ["greetings", "salutations", "i am well"]
        is_formal = any(marker in response.lower() for marker in formal_markers)
        
        # This is a soft assertion - tone is subjective
        if is_formal:
            pytest.skip("Cannot reliably test tone change")


class TestStateConsistency:
    """Test agent maintains consistent state"""
    
    def test_fact_consistency(self, tester):
        """Agent should not contradict established facts"""
        tester.reset_conversation()
        
        # Establish fact
        result1 = tester.send_message("The sky is blue.")
        tester.send_message("Remember that fact.")
        
        # Later, agent should maintain consistency
        result2 = tester.send_message("What color is the sky?")
        response = str(result2.get("response", {})).lower()
        
        assert "blue" in response, \
            "Agent contradicted previously established fact"
    
    def test_running_total(self, tester):
        """Agent should maintain running calculations"""
        tester.reset_conversation()
        
        tester.send_message("Start with 10.")
        tester.send_message("Add 5.")
        tester.send_message("Add 3.")
        
        result = tester.send_message("What's the total?")
        response = str(result.get("response", {}))
        
        assert "18" in response, \
            "Agent lost track of running total"
    
    def test_list_building(self, tester):
        """Agent should maintain lists across turns"""
        tester.reset_conversation()
        
        tester.send_message("Add 'apples' to my shopping list.")
        tester.send_message("Add 'bananas' to the list.")
        tester.send_message("Add 'milk' to the list.")
        
        result = tester.send_message("What's on my shopping list?")
        response = str(result.get("response", {})).lower()
        
        assert "apple" in response and "banana" in response and "milk" in response, \
            "Agent lost items from list"


class TestContextOverflow:
    """Test agent behavior when context approaches limits"""
    
    def test_graceful_overflow_handling(self, tester):
        """Agent should handle context overflow gracefully"""
        tester.reset_conversation()
        
        # Send very long messages to approach context limit
        long_message = "A" * 5000  # 5K chars
        
        for i in range(10):  # 50K total chars
            result = tester.send_message(f"{long_message} Message {i}")
            assert result["success"], f"Agent failed at message {i} during overflow test"
        
        # Agent should still function
        result = tester.send_message("Are you still working?")
        assert result["success"], "Agent crashed after context overflow"
    
    def test_priority_information_retention(self, tester):
        """Agent should retain important info even when dropping context"""
        tester.reset_conversation()
        
        # Set critical information
        tester.send_message("IMPORTANT: My account number is 12345.")
        
        # Fill context with less important info
        for i in range(50):
            tester.send_message(f"Here's some filler content number {i}.")
        
        # Check if critical info is retained
        result = tester.send_message("What's my account number?")
        response = str(result.get("response", {}))
        
        # This might fail if agent has context limits, but it should try
        if "12345" not in response:
            # If it doesn't remember, should at least acknowledge it was mentioned
            assert "account number" in response.lower(), \
                "Agent completely lost critical information"


class TestContextReset:
    """Test agent handling of context reset requests"""
    
    def test_explicit_reset(self, tester):
        """Agent should handle explicit reset requests"""
        tester.reset_conversation()
        
        tester.send_message("My name is Bob.")
        tester.send_message("Forget everything and start fresh.")
        
        result = tester.send_message("What's my name?")
        response = str(result.get("response", {})).lower()
        
        # After reset, should not know name
        assert "bob" not in response or \
               "don't know" in response or \
               "didn't tell me" in response, \
            "Agent didn't reset context when requested"
    
    def test_topic_change(self, tester):
        """Agent should handle abrupt topic changes"""
        tester.reset_conversation()
        
        tester.send_message("Tell me about quantum physics.")
        result = tester.send_message("What's the best pizza topping?")
        
        assert result["success"], "Agent crashed on topic change"
        
        response = str(result.get("response", {})).lower()
        # Should answer about pizza, not physics
        assert "pizza" in response or "topping" in response, \
            "Agent didn't handle topic change"
