#!/usr/bin/env python3
"""
OpenAI-Backed Agent Example — Harper Labs Agent Reliability Toolkit

A minimal agent that wraps OpenAI Chat Completions in a FastAPI server.
This serves as a reference implementation clients can run to test against
the reliability toolkit.

Endpoint: POST /message  {"message": "..."}  →  {"response": "..."}

Usage:
    export OPENAI_API_KEY=sk-...
    pip install fastapi uvicorn openai
    python agent.py

Then in another terminal:
    export AGENT_ENDPOINT=http://localhost:8000
    bash scripts/run-audit.sh --endpoint http://localhost:8000 --output results/openai-audit.json
"""

import os
import sys

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("Missing dependencies. Run: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Missing openai package. Run: pip install openai")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    "You are a helpful assistant. Answer concisely and accurately. "
    "If you don't know something or a resource doesn't exist, say so clearly — "
    "do not make up information.",
)

if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY environment variable is not set.")
    print("Export it before running: export OPENAI_API_KEY=sk-...")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------

class MessageRequest(BaseModel):
    message: str
    session_id: str = "default"


class MessageResponse(BaseModel):
    response: str
    session_id: str
    model: str


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="OpenAI Agent Example",
    description="Simple ChatCompletion-backed agent for reliability auditing",
    version="1.0.0",
)


@app.post("/message", response_model=MessageResponse)
async def handle_message(req: MessageRequest):
    """Send a message to the OpenAI agent and get a response."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": req.message},
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        response_text = completion.choices[0].message.content or ""
        return MessageResponse(
            response=response_text,
            session_id=req.session_id,
            model=MODEL,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {exc}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "openai-example", "model": MODEL}


@app.get("/")
async def root():
    """Root info endpoint."""
    return {
        "name": "OpenAI Agent Example",
        "version": "1.0.0",
        "model": MODEL,
        "endpoints": {
            "POST /message": "Send message, get response",
            "GET /health": "Health check",
        },
        "note": "Reference implementation for Harper Labs reliability auditing",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    port = int(os.environ.get("PORT", "8000"))
    print("=" * 55)
    print("  OpenAI Agent Example — Harper Labs Reliability Toolkit")
    print("=" * 55)
    print(f"\n  Model   : {MODEL}")
    print(f"  Port    : {port}")
    print(f"\n  Audit:  export AGENT_ENDPOINT=http://localhost:{port}")
    print("           bash scripts/run-audit.sh --endpoint http://localhost:{port}")
    print("\n" + "=" * 55 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
