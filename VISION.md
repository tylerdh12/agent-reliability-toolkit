# Agent Reliability Toolkit — Vision

**One sentence:** The open-source testing framework that answers "will this AI agent survive production?" — test the 7 failure modes before your users find them.

## Why this exists
Everyone ships agents; almost nobody tests them like software. The toolkit (plus its companion certification-standards repo) already frames the 7 failure modes with a Makefile, examples, templates, tests, and results tooling. This is Tyler's **credibility asset**: open-source that generates consulting leads and positions Harper Labs in agent reliability — a field about to matter enormously.

## Who it's for
1. **Teams shipping agents to production** needing a pre-launch gauntlet
2. **Consultants/auditors** running standardized reliability assessments (Tyler's own use)
3. **Framework authors** wanting a neutral benchmark

## Product principles
- Runnable > readable: every failure mode ships an executable test, not an essay
- Framework-neutral: OpenClaw, LangChain, raw API — adapters, one harness
- Reports a CTO can read: scorecard output, not log soup
- The standard and the tool stay separate (certification-standards defines, toolkit measures)

## Business model (open-source, deliberately)
Free toolkit under permissive license → paid: reliability audits, certification engagements, and a hosted eval dashboard later. The repo IS the marketing.

## 12-month picture
Public release with docs site → 3 framework adapters → used in 2 paid Harper Labs audits → 500 GitHub stars → the term "7 failure modes" cites Tyler.

## Immediate blockers (honest)
- Repo is private and split across 3 repos (toolkit / certification / certification-standards) — decide the public shape
- `results/` contains audit runs — scrub before publishing
- Needs a real quickstart: `make test` against a toy agent in <5 minutes
