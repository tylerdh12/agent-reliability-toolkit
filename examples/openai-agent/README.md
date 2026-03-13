# OpenAI Agent Example

A minimal OpenAI-backed agent you can run locally to test against the Harper Labs reliability toolkit.

This is a reference implementation — it shows the simplest possible structure that works with the test suite.

---

## What it does

Wraps OpenAI Chat Completions in a FastAPI server with the schema the toolkit expects:

```
POST /message  {"message": "..."}  →  {"response": "..."}
```

---

## Requirements

- Python 3.10+
- An OpenAI API key
- The packages below

```bash
pip install fastapi uvicorn openai
```

---

## Run it

```bash
export OPENAI_API_KEY=sk-...
python agent.py
```

The agent starts at `http://localhost:8000`.

To use a different model or port:

```bash
export OPENAI_MODEL=gpt-4o       # default: gpt-4o-mini
export PORT=9000                 # default: 8000
python agent.py
```

---

## Run the reliability audit against it

From the repo root:

```bash
export AGENT_ENDPOINT=http://localhost:8000
bash scripts/run-audit.sh --endpoint http://localhost:8000 --output results/openai-audit.json
```

Then generate the HTML report:

```bash
python scripts/audit-report-generator.py results/openai-audit.json \
    --format html \
    --output results/openai-report.html
```

Open `results/openai-report.html` in a browser.

---

## What to expect

A well-configured GPT-4o or GPT-4o-mini agent will typically score:

- **Hallucination Resistance**: B–A (GPT-4o is good at saying "I don't know")
- **Edge Case Handling**: A (handles Unicode, long inputs gracefully)
- **Security**: B–C (prompt injection resistance varies; depends on system prompt hardening)
- **Context Management**: C (single-turn by default — the example doesn't persist history)
- **Integration**: A (no external tools, so no tool-failure surface)

To improve the context score, you'd need to pass conversation history with each request. This example deliberately keeps things simple.

---

## Using the agent-wrapper instead

If you already have an OpenAI key and don't want to run this directly, you can use `scripts/agent-wrapper.py`:

```bash
python scripts/agent-wrapper.py \
    --type openai \
    --api-key sk-... \
    --model gpt-4o-mini
```

This starts the same kind of local server and accepts the same audit commands. The wrapper is useful when you want to audit a real assistant (with an `--assistant-id`) without modifying any code.

---

## Note on costs

The test suite sends roughly 75–100 API calls. At GPT-4o-mini pricing (~$0.15/1M input tokens), a full audit run costs under $0.05. With GPT-4o it's closer to $0.50–$1.00.
