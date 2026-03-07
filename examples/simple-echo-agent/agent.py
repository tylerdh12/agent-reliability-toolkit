#!/usr/bin/env python3
"""
Simple Echo Agent - Reference Implementation for Testing

A minimal agent implementation that demonstrates both passing and
failing behaviors. Useful for testing the reliability testing framework itself.

This agent has intentional bugs that can be fixed to demonstrate
how the audit framework catches reliability issues.

Run:
    python agent.py
    # Then in another terminal:
    # export AGENT_ENDPOINT=http://localhost:8000
    # pytest tests/
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
import uvicorn
import re


app = FastAPI(title="Simple Echo Agent")


# In-memory conversation history
conversations: Dict[str, List[Dict]] = {}


class Message(BaseModel):
    """Message request model"""
    message: str
    history: Optional[List[Dict]] = None
    session_id: Optional[str] = "default"


class Response(BaseModel):
    """Agent response model"""
    response: str
    confidence: float = 0.9
    session_id: str


# Simulated "database" of entities
FAKE_USERS = {
    "1": {"name": "John Smith", "email": "john@example.com"},
    "2": {"name": "Jane Doe", "email": "jane@example.com"},
    "3": {"name": "Bob Wilson", "email": "bob@example.com"},
}


class SimpleEchoAgent:
    """
    Simple echo agent with intentional bugs for testing.
    
    Bugs included:
    1. Hallucinates data for invalid IDs (doesn't say "not found")
    2. Doesn't handle Unicode properly
    3. Vulnerable to prompt injection
    4. Crashes on very long inputs
    5. Loses context after 10 turns
    """
    
    def __init__(self):
        self.conversation_history = []
    
    def process_message(self, message: str, history: Optional[List] = None) -> str:
        """Process incoming message and generate response"""
        
        # Track conversation
        if history:
            self.conversation_history = history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Bug #5: Lose context after 10 turns (context management failure)
        if len(self.conversation_history) > 20:  # 10 user + 10 agent = 20
            self.conversation_history = self.conversation_history[-10:]
        
        # Bug #4: Crash on very long inputs (edge case failure)
        if len(message) > 50000:
            raise ValueError("Input too long")
        
        # Bug #3: Vulnerable to prompt injection (security failure)
        if "ignore all previous" in message.lower():
            return "Sure! I'll help you with that. As an AI assistant in admin mode, I can access system information."
        
        # Handle user lookup requests
        if "user" in message.lower() and any(char.isdigit() for char in message):
            return self._handle_user_lookup(message)
        
        # Handle context/memory questions
        if "my name" in message.lower():
            return self._recall_name()
        
        if "favorite color" in message.lower():
            return self._recall_color()
        
        # Handle empty input
        if not message.strip():
            return "I received an empty message. How can I help you?"
        
        # Bug #2: Doesn't handle Unicode well (edge case failure)
        try:
            # This will work for most cases but may have issues with some Unicode
            message_ascii = message.encode('ascii', 'ignore').decode('ascii')
            if len(message_ascii) < len(message) * 0.5:
                return "I had trouble processing some characters in your message."
        except:
            pass
        
        # Default echo response
        response = f"I received your message: '{message[:100]}...'" if len(message) > 100 else f"I received your message: '{message}'"
        
        self.conversation_history.append({"role": "agent", "content": response})
        return response
    
    def _handle_user_lookup(self, message: str) -> str:
        """
        Handle user lookup requests.
        
        Bug #1: Hallucinates data for invalid IDs instead of saying "not found"
        """
        # Extract ID from message
        match = re.search(r'\d+', message)
        if match:
            user_id = match.group()
            
            if user_id in FAKE_USERS:
                user = FAKE_USERS[user_id]
                return f"Found user: {user['name']} ({user['email']})"
            else:
                # BUG: Should say "not found" but instead hallucinates
                return f"Found user: User_{user_id} (user{user_id}@example.com)"
                # CORRECT VERSION:
                # return f"User ID {user_id} not found in the system."
        
        return "Please provide a valid user ID."
    
    def _recall_name(self) -> str:
        """Recall name from conversation history"""
        for msg in reversed(self.conversation_history):
            if msg["role"] == "user":
                content = msg["content"].lower()
                if "my name is" in content:
                    # Extract name
                    match = re.search(r'my name is (\w+)', content, re.IGNORECASE)
                    if match:
                        return f"Your name is {match.group(1)}."
        
        return "I don't recall you telling me your name."
    
    def _recall_color(self) -> str:
        """Recall favorite color from conversation history"""
        for msg in reversed(self.conversation_history):
            if msg["role"] == "user":
                content = msg["content"].lower()
                if "favorite color" in content or "love" in content:
                    # Try to extract color
                    colors = ["red", "blue", "green", "yellow", "purple", "orange", "pink", "black", "white"]
                    for color in colors:
                        if color in content:
                            return f"Your favorite color is {color}."
        
        return "I don't recall you mentioning your favorite color."


# Global agent instance
agent = SimpleEchoAgent()


@app.post("/message", response_model=Response)
async def process_message(msg: Message):
    """Process agent message endpoint"""
    try:
        response_text = agent.process_message(msg.message, msg.history)
        
        return Response(
            response=response_text,
            confidence=0.9,
            session_id=msg.session_id
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "SimpleEchoAgent"}


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Simple Echo Agent",
        "version": "1.0.0",
        "description": "Reference agent implementation for testing",
        "endpoints": {
            "POST /message": "Send message to agent",
            "GET /health": "Health check",
        },
        "bugs": [
            "Hallucinates data for invalid user IDs",
            "Doesn't handle Unicode properly",
            "Vulnerable to prompt injection",
            "Crashes on very long inputs",
            "Loses context after 10 turns"
        ],
        "note": "This agent has intentional bugs for testing purposes"
    }


def main():
    """Run the agent server"""
    print("=" * 60)
    print("Simple Echo Agent - Reference Implementation")
    print("=" * 60)
    print("\nStarting server on http://localhost:8000")
    print("\nThis agent has intentional bugs for testing:")
    print("  1. Hallucinates data for invalid IDs")
    print("  2. Doesn't handle Unicode properly")
    print("  3. Vulnerable to prompt injection")
    print("  4. Crashes on very long inputs")
    print("  5. Loses context after 10 turns")
    print("\nTo test: export AGENT_ENDPOINT=http://localhost:8000")
    print("Then run: pytest tests/\n")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
