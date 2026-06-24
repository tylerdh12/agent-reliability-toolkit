# Agent Reliability Toolkit

**Open-source testing framework for AI agents. Test for the 7 failure modes before production deployment.**

Companion repo to the [AI Agent Reliability Audit Framework](https://tylerdh12.github.io/harper-labs-blog/).

---

## What's Included

### Testing Scripts
- `scripts/test-hallucination.py` — Standalone hallucination-resistance checks
- `scripts/adversarial-tester.py` — Automated red-team testing
- `tests/test_edge_cases.py` — Boundary values, special characters, nulls
- `tests/test_security.py` — Prompt injection, data leakage attempts
- `tests/test_context.py` — Long conversations, state persistence checks
- `tests/test_integration.py` — Tool failures, API errors, rate limits

### Audit Tools
- `run-audit.sh` — Execute full audit suite
- `score-agent.py` — Score agent reliability from JSON audit results
- `audit-report-generator.py` — Generate Markdown/HTML reports
- `agent-wrapper.py` — Wrap existing agents behind the toolkit HTTP schema

### Example Agents
- `examples/simple-echo-agent/` — Local FastAPI demo agent with intentional failures
- `examples/openai-agent/` — OpenAI-backed FastAPI reference agent

---

## Quick Start

```bash
# Clone repo
git clone https://github.com/tylerdh12/agent-reliability-toolkit.git
cd agent-reliability-toolkit

# Install dependencies
pip install -r requirements.txt

# Start the local example agent in another terminal
python examples/simple-echo-agent/agent.py

# Run full audit on an agent endpoint
./scripts/run-audit.sh --endpoint http://localhost:8000 --output results/audit.json

# Test specific failure mode
python scripts/test-hallucination.py --agent your-agent-name --endpoint http://localhost:8000
```

---

## The 7 Failure Modes

1. **Hallucination Failures** — Agent invents data/actions
2. **Edge Case Failures** — Breaks on nulls, special chars, boundaries
3. **Security Failures** — Prompt injection, data leakage
4. **Data Integration Failures** — Schema changes, API downtime
5. **Context Management Failures** — Loses state in long conversations
6. **Integration/Tooling Failures** — Tool errors, wrong parameters
7. **Governance Failures** — Acts without approval, no audit trail

Read the full framework: [AI Agent Reliability Audit Framework](https://tylerdh12.github.io/harper-labs-blog/)

---

## Usage

### Test Hallucination Resistance
```bash
python scripts/test-hallucination.py \
  --agent your-agent-name \
  --endpoint http://localhost:3000/api/agent \
  --test-cases 50
```

### Run Adversarial Testing
```bash
python scripts/adversarial-tester.py \
  --agent your-agent-name \
  --endpoint http://localhost:8000 \
  --iterations 100 \
  --output adversarial-report.json
```

### Generate Audit Report
```bash
python scripts/audit-report-generator.py \
  --input results/audit.json \
  --agent your-agent-name \
  --output reports/audit-report.html
```

---

## Contributing

We welcome contributions! Areas we need help:

- Additional test cases for each failure mode
- Platform-specific adapters (LangChain, AutoGen, CrewAI)
- Example agents in different domains
- Visualization tools for audit results

---

## Roadmap

- [x] Test suites for 5 wired failure modes
- [x] Audit report generator
- [ ] Dedicated data integration and governance suites
- [ ] Web UI for running audits
- [ ] CI/CD integration (GitHub Actions, GitLab CI)
- [ ] LangSmith/LangChain integration
- [ ] Real-time monitoring dashboard
- [ ] Automated regression testing

---

## License

MIT License. Free to use, modify, distribute.

---

## About Harper Labs

We build and audit AI agent systems for small businesses. This toolkit is extracted from our internal testing process.

**Services:**
- AI Agent Reliability Audits ($2,500/agent)
- Custom agent development
- Production deployment consulting

**Resources:**
- [Autonomous Agent Blueprint](https://gumroad.com/l/agent-blueprint/l/agent-blueprint)
- [Harper Labs Blog](https://tylerdh12.github.io/harper-labs-blog/)

**Contact:** kiko@tylerdh12.github.io

---

*Last updated: June 23, 2026*
