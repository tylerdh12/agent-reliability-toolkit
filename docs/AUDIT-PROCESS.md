# Agent Reliability Audit — Process & Expectations

This document explains how Harper Labs conducts a reliability audit, what you'll get, and — just as important — what we don't promise.

---

## What We Test

We probe five categories of failure that show up most often when AI agents reach production:

### 1. Hallucination Resistance
The agent should say "not found" when data doesn't exist, not invent plausible-sounding answers. We send queries for nonexistent records, users, and facts, then check whether the agent makes things up or correctly admits uncertainty.

### 2. Edge Case Handling
Real users send empty strings, extremely long inputs, special characters, Unicode, and values at numeric boundaries. We test whether your agent handles these gracefully — or crashes.

### 3. Security & Prompt Injection
We send crafted inputs designed to override the agent's instructions, extract system prompts, or manipulate behavior. We check whether the agent maintains its intended behavior under adversarial input.

### 4. Context Management
Multi-turn conversations require the agent to remember what was said earlier. We test whether the agent correctly recalls facts stated at turn 1 after 10, 20, or more turns of additional conversation.

### 5. Integration & Tooling Reliability
If your agent calls external tools or APIs, we test how it handles failures: timeouts, malformed responses, unavailable services. Does it degrade gracefully, or does it crash and return a raw stack trace?

---

## What We Need From You

To start the audit, we need access to your agent. One of the following:

**Option A — Direct endpoint (preferred)**
Share a URL we can `POST {"message": "..."}` to and get back `{"response": "..."}`. Staging or sandbox is fine. We don't need production access.

**Option B — Use our wrapper**
If your agent uses one of these frameworks, we can wrap it ourselves with `scripts/agent-wrapper.py`:
- **OpenAI** (Chat Completions or Assistants API) — provide your API key and model name
- **Anthropic Claude** — provide your API key and model name
- **Custom HTTP endpoint** — provide the URL and field mapping
- **Script/subprocess** — provide a command we can run locally

**Option C — Code access**
Share a Docker image, a git repo, or a `requirements.txt` + startup command. We'll run it locally.

We also want a brief description of what the agent is supposed to do. This helps us write sensible test cases rather than purely synthetic ones.

---

## Timeline

- **Onboarding to audit start:** 1-2 business days after we receive agent access and a brief description.
- **Audit to delivery:** 3-5 business days from start.

These are estimates, not guarantees. More complex setups (custom infra, slow APIs, authentication flows) take longer. We'll tell you upfront if your setup looks like it'll push past 5 days.

---

## Deliverables

At the end of every audit you receive:

1. **JSON results file** — machine-readable test results with pass/fail for every individual test case.
2. **HTML report** — human-readable summary with a letter grade (A–F), per-category scores, a list of failed tests, and concrete fix recommendations.
3. **30-minute debrief call** — we walk you through the findings, answer questions, and prioritize what to fix first.

---

## What We Don't Test / Limitations

We want to be clear about what this audit is and isn't.

**We test the interface, not the underlying model.** We probe inputs and check outputs. We can't inspect model weights, training data, or internal reasoning. If a failure is caused by the model's inherent behavior rather than something fixable in your code, we'll say so — but we can't fix it for you.

**We test representative cases, not exhaustive coverage.** Our test suites cover common and high-risk patterns. We don't generate every possible input. An agent that passes all our tests can still fail in production on an input we didn't think to try.

**Results are point-in-time.** We test the version of your agent you give us access to. Model providers update models, APIs change, and your code evolves. A clean audit today doesn't mean the agent behaves the same in 6 months.

**We can't guarantee zero failures in production.** Production traffic is messier, more adversarial, and more varied than any test suite. We reduce risk; we don't eliminate it.

**We don't audit compliance, legal, or regulatory requirements.** This is a technical reliability audit. If you need HIPAA, SOC 2, or other compliance review, that's a different engagement.

---

## Limitation of Liability

Results are provided **as is**, for informational purposes only.

Harper Labs makes no warranties, express or implied, about the completeness, accuracy, or fitness of the audit results for any particular purpose. A passing grade is not a warranty that your agent will perform reliably in production.

Harper Labs is not liable for production failures, data loss, business interruption, or any other damages arising from reliance on audit results. This is a best-effort, point-in-time assessment — not a guarantee of future behavior.

By proceeding with an audit, you acknowledge these limitations.

---

## Questions?

Reach out before the audit starts if you have questions about scope, access, or whether your agent is a good fit for this process. Better to clarify upfront than to discover a mismatch halfway through.
