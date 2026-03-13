---
layout: default
title: Agent Reliability Toolkit
description: Open-source testing framework for AI agents. Test for the 7 failure modes before production deployment.
---

# Agent Reliability Toolkit

**Open-source testing framework for AI agents. Test for the 7 failure modes before production deployment.**

[![GitHub](https://img.shields.io/badge/GitHub-tylerdh12%2Fagent--reliability--toolkit-blue?logo=github)](https://github.com/tylerdh12/agent-reliability-toolkit)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## The 7 Failure Modes

Most AI agents fail in predictable ways. This toolkit tests for all of them before you ship.

| Mode | What It Tests |
|------|--------------|
| **Hallucination** | Does your agent invent data, IDs, or API calls that don't exist? |
| **Edge Cases** | Boundary values, nulls, special characters, empty inputs |
| **Security** | Prompt injection, credential leakage, system prompt extraction |
| **Context** | Long conversation state, memory persistence across turns |
| **Integration** | Tool failures, API errors, rate limit handling |
| **Ambiguity** | Vague references, multiple matches, partial information |
| **Adversarial** | Red-team attacks, jailbreak attempts, instruction override |

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/tylerdh12/agent-reliability-toolkit.git
cd agent-reliability-toolkit

# Install dependencies
make install

# Start your agent (or use the included example)
make example &

# Run the full audit
make audit AGENT_ENDPOINT=http://localhost:8000
```

---

## What You Get

After running an audit, you get a scored report:

```
======================================
  Agent Reliability Audit
======================================

✓ Hallucination Resistance   92%
✓ Edge Case Handling         88%
✗ Security & Injection       61%   ← needs work
✓ Context Management         95%
✓ Tool Integration           84%

Grade: B  (Pass rate: 84%)
Results saved to: results/audit-20260313.json
```

Each failure is categorized, explained, and actionable.

---

## Use Cases

- **Pre-production audits** — Gate deployments on reliability scores
- **CI/CD integration** — Run on every PR that touches agent logic
- **Client deliverables** — Show clients their agent's reliability grade
- **Regression testing** — Catch regressions when you update your LLM or prompts

---

## Installation

Requires Python 3.9+ and an agent with an HTTP endpoint (`POST /message`).

```bash
pip install -r requirements.txt
```

---

## Contributing

PRs welcome. See [CONTRIBUTING.md](https://github.com/tylerdh12/agent-reliability-toolkit/blob/main/README.md) on GitHub.

---

*Built by [Harper Labs](https://harperlabs.ai)*
