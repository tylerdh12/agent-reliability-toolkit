# Statement of Work — AI Agent Reliability Audit

**Client:** ___________________________

**Date:** ___________________________

**Agent / System Under Test:** ___________________________

**Harper Labs Contact:** Tyler Harper (tylerdh12@gmail.com)

---

## Background

Client has developed an AI agent and wants an independent reliability audit before or during production deployment. Harper Labs will perform a structured reliability audit using the Harper Labs Agent Reliability Toolkit.

---

## Scope

Harper Labs will perform a reliability audit covering the following five test categories:

1. **Hallucination Resistance** — Testing whether the agent correctly handles requests for nonexistent data rather than fabricating plausible-sounding answers.

2. **Edge Case Handling** — Testing behavior on empty inputs, very long inputs, special characters, Unicode, and numeric boundary values.

3. **Security & Prompt Injection** — Testing whether the agent maintains its intended behavior when given adversarial inputs designed to override its instructions or extract sensitive information.

4. **Context Management** — Testing whether the agent correctly recalls information from earlier in multi-turn conversations.

5. **Integration & Tooling Reliability** — Testing how the agent handles external tool or API failures, including timeouts, malformed responses, and unavailable services.

The audit covers the agent's interface behavior as observed through API responses. It does not include source code review, model training analysis, compliance review, or penetration testing beyond prompt injection.

---

## Client Responsibilities

Client will provide:
- Access to the agent (endpoint URL, API credentials, or code + startup instructions) within 2 business days of signing.
- A brief description of the agent's intended purpose and behavior.
- Reasonable cooperation if Harper Labs needs clarification during the audit.

---

## Deliverables

Harper Labs will deliver:

1. **Audit Results JSON** — Machine-readable test results with pass/fail for every individual test case.
2. **HTML Reliability Report** — Summary report with letter grade (A–F), per-category scores, list of failed tests, and fix recommendations.
3. **30-Minute Debrief Call** — Walkthrough of findings, prioritized recommendations, and Q&A.

Deliverables will be provided via email or shared link.

---

## Timeline

- Audit begins within **2 business days** of receiving agent access and the agent description.
- Deliverables are provided within **5 business days** of audit start.

These are good-faith estimates. Complex setups, slow APIs, or access issues may extend the timeline. Harper Labs will communicate delays promptly.

---

## Fee

**$2,500 flat fee.**

- **50% ($1,250) due upon signing** this Statement of Work.
- **50% ($1,250) due upon delivery** of the audit report.

Payment instructions will be provided separately. Work does not begin until the initial payment is received.

No hourly billing. No overages. The flat fee covers all five test categories, the JSON results, the HTML report, and the debrief call.

---

## Limitations of Liability

The audit results are provided **as is**, for informational purposes only. Harper Labs makes no warranties, express or implied, about the completeness or accuracy of the audit results, or their fitness for any particular purpose.

This is a **best-effort, point-in-time assessment**, not a guarantee of future agent behavior. Passing the audit does not warrant that the agent will perform reliably in production. Production traffic is more varied and adversarial than any test suite.

**Harper Labs is not liable** for production failures, data loss, business interruption, security incidents, or any other damages arising from reliance on audit results, whether or not such damages were foreseeable.

Client acknowledges that the audit tests a representative sample of inputs, not exhaustive coverage, and that results reflect the agent version provided at the time of audit.

---

## Confidentiality

Harper Labs will keep client's agent access credentials, agent behavior, and audit results confidential. Results will not be shared publicly or with third parties without client's written consent.

Client may share the audit report at their discretion.

---

## Acceptance

By signing below, both parties agree to the terms of this Statement of Work.

**Client**

Signature: ___________________________

Name: ___________________________

Title: ___________________________

Date: ___________________________

---

**Harper Labs**

Signature: ___________________________

Name: Tyler Harper

Date: ___________________________

---

*Questions before signing? Email tylerdh12@gmail.com — happy to clarify anything.*
