# Agent Reliability Toolkit

**Open-source testing framework for AI agents. Test for the 7 failure modes before production deployment.**

Companion repo to the [AI Agent Reliability Audit Framework](https://tylerdh12.github.io/harper-labs-blog/).

---

## What's Included

### Testing Scripts
- `test-hallucination.py` — Test agent responses to invalid/missing data
- `test-edge-cases.sh` — Boundary values, special characters, nulls
- `test-security.py` — Prompt injection, data leakage attempts
- `test-context.py` — Long conversations, state persistence checks
- `test-integration.py` — Tool failures, API errors, rate limits
- `adversarial-tester.py` — Automated red-team testing

### Audit Tools
- `run-audit.sh` — Execute full audit suite
- `audit-report-generator.py` — Score agent, generate PDF report
- `failure-classifier.py` — Categorize failures by mode

### Example Agents
- `examples/email-agent/` — Audited email triage agent (passing example)
- `examples/calendar-agent/` — Calendar management agent
- `examples/data-pipeline/` — Data integration agent

---

## Quick Start

```bash
# Clone repo
git clone https://github.com/tylerdh12/agent-reliability-toolkit.git
cd agent-reliability-toolkit

# Install dependencies
pip install -r requirements.txt

# Run full audit on your agent
./scripts/run-audit.sh --agent your-agent-name --output report.pdf

# Test specific failure mode
python scripts/test-hallucination.py --agent your-agent-name
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
  --iterations 100 \
  --output adversarial-report.json
```

### Generate Audit Report
```bash
python scripts/audit-report-generator.py \
  --test-results ./results/ \
  --output audit-report.pdf
```

---

## Contributing

We welcome contributions! Areas we need help:

- Additional test cases for each failure mode
- Platform-specific adapters (LangChain, AutoGen, CrewAI)
- Example agents in different domains
- Visualization tools for audit results

See `CONTRIBUTING.md` for guidelines.

---

## Roadmap

- [x] Test scripts for 7 failure modes
- [x] Audit report generator
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

**Contact:** kiko@tylerharper.dev

---

*Last updated: March 7, 2026*
