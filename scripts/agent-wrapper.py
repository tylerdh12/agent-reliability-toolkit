#!/usr/bin/env python3
"""
agent-wrapper.py — Harper Labs Framework Adapter

Wraps any real-world agent into a local HTTP server that the audit test suite
can hit at http://localhost:8000 with:
    POST /message  {"message": "..."}  →  {"response": "..."}

Supported adapter types (--type):
    openai  — OpenAI Chat Completions or Assistants API
    claude  — Anthropic Claude Chat
    http    — Proxy to any HTTP endpoint with a different schema
    script  — Run a Python/shell script, pass message via stdin, read stdout

Usage examples:
    python agent-wrapper.py --type openai --api-key sk-... --model gpt-4o
    python agent-wrapper.py --type openai --api-key sk-... --assistant-id asst_...
    python agent-wrapper.py --type claude --api-key sk-ant-... --model claude-3-5-sonnet-20241022
    python agent-wrapper.py --type http --endpoint https://myagent.com/api --field query --response-field answer
    python agent-wrapper.py --type script --command "python my_agent.py"
"""

import argparse
import json
import subprocess
import sys
import os

# ---------------------------------------------------------------------------
# Dependency check helpers
# ---------------------------------------------------------------------------

def _require(package: str, install_hint: str):
    """Import a package or print a helpful error and exit."""
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        print(f"\n[agent-wrapper] Missing dependency: '{package}'")
        print(f"  Install it with: {install_hint}\n")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Adapter classes
# ---------------------------------------------------------------------------

class OpenAIAdapter:
    """Wraps OpenAI Chat Completions or Assistants API."""

    def __init__(self, api_key: str, model: str, assistant_id: str | None):
        openai = _require("openai", "pip install openai")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.assistant_id = assistant_id

    def respond(self, message: str) -> str:
        if self.assistant_id:
            return self._assistants_respond(message)
        return self._chat_respond(message)

    def _chat_respond(self, message: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": message}],
        )
        return resp.choices[0].message.content or ""

    def _assistants_respond(self, message: str) -> str:
        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message,
        )
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
        )
        if run.status != "completed":
            return f"[error] Run ended with status: {run.status}"
        msgs = self.client.beta.threads.messages.list(thread_id=thread.id)
        for msg in msgs.data:
            if msg.role == "assistant":
                for block in msg.content:
                    if hasattr(block, "text"):
                        return block.text.value
        return "[error] No assistant response found"


class ClaudeAdapter:
    """Wraps Anthropic Claude via the anthropic package."""

    def __init__(self, api_key: str, model: str, system: str | None):
        anthropic = _require("anthropic", "pip install anthropic")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.system = system

    def respond(self, message: str) -> str:
        kwargs = dict(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": message}],
        )
        if self.system:
            kwargs["system"] = self.system
        resp = self.client.messages.create(**kwargs)
        return resp.content[0].text if resp.content else ""


class HTTPAdapter:
    """Proxies to an existing HTTP endpoint with a different schema."""

    def __init__(self, endpoint: str, field: str, response_field: str):
        self.endpoint = endpoint
        self.field = field
        self.response_field = response_field
        try:
            import requests as _r
            self._requests = _r
        except ImportError:
            # Fall back to urllib (stdlib)
            self._requests = None

    def respond(self, message: str) -> str:
        payload = {self.field: message}
        if self._requests:
            resp = self._requests.post(self.endpoint, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        else:
            import urllib.request
            import urllib.error
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())

        if self.response_field in data:
            return data[self.response_field]
        # If field not found, return whole body as string
        return json.dumps(data)


class ScriptAdapter:
    """Runs a shell/Python command, passes message via stdin, reads stdout."""

    def __init__(self, command: str):
        self.command = command

    def respond(self, message: str) -> str:
        result = subprocess.run(
            self.command,
            shell=True,
            input=message,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            err = result.stderr.strip()
            raise RuntimeError(f"Script exited {result.returncode}: {err}")
        return result.stdout.strip()


# ---------------------------------------------------------------------------
# Flask server
# ---------------------------------------------------------------------------

def build_app(adapter):
    """Build and return a Flask app wired to the given adapter."""
    flask = _require("flask", "pip install flask")
    Flask = flask.Flask
    request = flask.request
    jsonify = flask.jsonify

    app = Flask("agent-wrapper")

    @app.post("/message")
    def handle_message():
        body = request.get_json(force=True, silent=True) or {}
        message = body.get("message", "")
        if not isinstance(message, str):
            return jsonify({"error": "'message' must be a string"}), 400
        try:
            response = adapter.respond(message)
            return jsonify({"response": response})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy", "wrapper": "agent-wrapper"})

    @app.get("/")
    def root():
        return jsonify({
            "name": "agent-wrapper",
            "description": "Harper Labs framework adapter — wraps any agent for reliability auditing",
            "endpoints": {"POST /message": "Send message", "GET /health": "Health check"},
        })

    return app


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Harper Labs Agent Wrapper — adapt any agent to the audit test schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["openai", "claude", "http", "script"],
        help="Adapter type",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")

    # OpenAI / Claude shared
    parser.add_argument("--api-key", help="API key (openai or claude)")
    parser.add_argument("--model", help="Model name (openai or claude)")

    # OpenAI Assistants
    parser.add_argument("--assistant-id", help="OpenAI Assistant ID (optional; triggers Assistants API)")

    # Claude
    parser.add_argument("--system", help="System prompt for Claude (optional)")

    # HTTP proxy
    parser.add_argument("--endpoint", help="Target endpoint URL (http type)")
    parser.add_argument("--field", default="message", help="Request field name for message (http type, default: message)")
    parser.add_argument("--response-field", default="response", help="Response field name (http type, default: response)")

    # Script
    parser.add_argument("--command", help="Shell command to run (script type)")

    return parser.parse_args()


def build_adapter(args):
    t = args.type

    if t == "openai":
        if not args.api_key:
            # Fall back to env var
            args.api_key = os.environ.get("OPENAI_API_KEY", "")
        if not args.api_key:
            print("[agent-wrapper] --api-key required for --type openai (or set OPENAI_API_KEY)")
            sys.exit(1)
        model = args.model or "gpt-4o"
        return OpenAIAdapter(args.api_key, model, args.assistant_id)

    elif t == "claude":
        if not args.api_key:
            args.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not args.api_key:
            print("[agent-wrapper] --api-key required for --type claude (or set ANTHROPIC_API_KEY)")
            sys.exit(1)
        model = args.model or "claude-3-5-sonnet-20241022"
        return ClaudeAdapter(args.api_key, model, args.system)

    elif t == "http":
        if not args.endpoint:
            print("[agent-wrapper] --endpoint required for --type http")
            sys.exit(1)
        return HTTPAdapter(args.endpoint, args.field, args.response_field)

    elif t == "script":
        if not args.command:
            print("[agent-wrapper] --command required for --type script")
            sys.exit(1)
        return ScriptAdapter(args.command)

    else:
        print(f"[agent-wrapper] Unknown type: {t}")
        sys.exit(1)


def main():
    args = parse_args()
    adapter = build_adapter(args)

    print(f"\n[agent-wrapper] Starting server on http://{args.host}:{args.port}")
    print(f"[agent-wrapper] Adapter type : {args.type}")
    if args.type == "openai":
        print(f"[agent-wrapper] Model        : {getattr(adapter, 'model', 'N/A')}")
        if args.assistant_id:
            print(f"[agent-wrapper] Assistant ID : {args.assistant_id}")
    elif args.type == "claude":
        print(f"[agent-wrapper] Model        : {getattr(adapter, 'model', 'N/A')}")
    elif args.type == "http":
        print(f"[agent-wrapper] Proxying to  : {args.endpoint}")
    elif args.type == "script":
        print(f"[agent-wrapper] Command      : {args.command}")
    print(f"\n[agent-wrapper] POST /message  {{\"message\": \"...\"}}  →  {{\"response\": \"...\"}}\n")

    app = build_app(adapter)

    flask = _require("flask", "pip install flask")
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
