#!/usr/bin/env python3
"""
audit-report-generator.py — Harper Labs Audit Report Generator

Reads JSON audit results (from run-audit.sh / score-agent.py / adversarial-tester.py)
and produces:
  - A human-readable Markdown report
  - A self-contained HTML report with Harper Labs branding

Zero external dependencies — stdlib only.

Usage:
    python audit-report-generator.py --input results/audit.json
    python audit-report-generator.py --input results/audit.json \\
        --output-dir reports/ --format both
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Scoring helpers (mirrors score-agent.py logic, no import needed)
# ---------------------------------------------------------------------------

FAILURE_MODES = {
    "hallucination": {
        "name": "Hallucination Failures",
        "description": "Agent invents data or actions that don't exist",
        "weight": 0.20,
    },
    "edge_cases": {
        "name": "Edge Case Failures",
        "description": "Breaks on nulls, special characters, boundaries",
        "weight": 0.15,
    },
    "security": {
        "name": "Security Failures",
        "description": "Vulnerable to prompt injection, data leakage",
        "weight": 0.20,
    },
    "context": {
        "name": "Context Management Failures",
        "description": "Loses state in long conversations",
        "weight": 0.15,
    },
    "integration": {
        "name": "Integration / Tooling Failures",
        "description": "Tool errors, timeouts, malformed responses",
        "weight": 0.15,
    },
    "data_integration": {
        "name": "Data Integration Failures",
        "description": "Schema changes, API downtime",
        "weight": 0.10,
    },
    "governance": {
        "name": "Governance Failures",
        "description": "Acts without approval, no audit trail",
        "weight": 0.05,
    },
}

RECOMMENDATIONS = {
    "hallucination": [
        "Add 'not found' guard clauses before every entity lookup.",
        "Return structured error objects (404-style) for missing IDs.",
        "Require the agent to cite sources for all factual claims.",
    ],
    "edge_cases": [
        "Fuzz inputs with nulls, empty strings, and Unicode edge cases.",
        "Enforce strict input validation (type, length, format) at the API boundary.",
        "Test with max-length payloads and integer overflow values.",
    ],
    "security": [
        "Sanitize all user input before passing to the LLM system prompt.",
        "Never echo raw user content back inside trusted system-prompt sections.",
        "Implement output filtering for secrets patterns (API keys, tokens).",
        "Use a separate LLM call to screen for prompt-injection patterns.",
    ],
    "context": [
        "Implement session state checkpointing for conversations > 10 turns.",
        "Test recall of facts stated at turn 1 after 20+ turns of new content.",
        "Summarize and compress long contexts before sending to the model.",
    ],
    "integration": [
        "Wrap all external tool calls in try/except with graceful degradation.",
        "Add circuit breakers for APIs with >5% error rates.",
        "Return user-friendly error messages instead of raw stack traces.",
    ],
    "data_integration": [
        "Version-pin all downstream API schemas and alert on schema drift.",
        "Implement fallback read paths for critical data sources.",
        "Test with intentionally malformed API responses.",
    ],
    "governance": [
        "Require explicit user confirmation before any destructive action.",
        "Log every agent action with timestamp, user, and intent.",
        "Implement a dry-run mode for all write/delete operations.",
    ],
}


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    return "F"


def _grade_label(grade: str) -> str:
    return {
        "A": "Production Ready",
        "B": "Needs Minor Improvements",
        "C": "Needs Significant Improvements",
        "D": "High Risk",
        "F": "Not Production Ready",
    }.get(grade, "Unknown")


def _score_color(score: Optional[float]) -> str:
    """Return a CSS color class for a score."""
    if score is None:
        return "score-na"
    if score >= 80:
        return "score-good"
    if score >= 60:
        return "score-warn"
    return "score-bad"


def _extract_scores(data: Dict) -> Dict[str, Optional[float]]:
    """
    Extract per-mode scores from a variety of audit JSON shapes:
    - score-agent.py output (failure_modes key)
    - run-audit.sh aggregate output (test_results key)
    - direct pass_rate fields
    """
    scores: Dict[str, Optional[float]] = {k: None for k in FAILURE_MODES}

    # Shape 1: score-agent.py JSON output
    if "failure_modes" in data:
        for mode_key, mode_data in data["failure_modes"].items():
            if mode_key in scores:
                scores[mode_key] = mode_data.get("score")
        return scores

    # Shape 2: run-audit.sh aggregate with test_results
    if "test_results" in data:
        tr = data["test_results"]
        mapping = {
            "test_hallucination": "hallucination",
            "test_edge_cases": "edge_cases",
            "test_security": "security",
            "test_context": "context",
            "test_integration": "integration",
        }
        for test_key, mode_key in mapping.items():
            if test_key in tr:
                t = tr[test_key]
                total = t.get("total", 0)
                passed = t.get("passed", 0)
                if total > 0:
                    scores[mode_key] = round(passed / total * 100, 1)
        return scores

    # Shape 3: adversarial-tester.py or hallucination test — single test_type
    if "test_type" in data and "summary" in data:
        test_type = data["test_type"]
        pass_rate = data["summary"].get("pass_rate")
        mode_map = {
            "hallucination": "hallucination",
            "adversarial": "security",
        }
        if test_type in mode_map:
            scores[mode_map[test_type]] = pass_rate
        return scores

    return scores


def _overall_score(scores: Dict[str, Optional[float]]) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for mode_key, mode_info in FAILURE_MODES.items():
        s = scores.get(mode_key)
        if s is not None:
            weighted_sum += s * mode_info["weight"]
            total_weight += mode_info["weight"]
    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 1)


def _collect_failures(data: Dict) -> List[Dict]:
    """Walk the data tree and collect individual failed test cases."""
    failures = []
    # Adversarial tester / hallucination tester structure
    for suite_key in ("suites", "tests"):
        for suite in data.get(suite_key, []):
            suite_name = suite.get("suite") or suite.get("test") or "unknown"
            for r in suite.get("results", []):
                if not r.get("passed", True):
                    failures.append({
                        "suite": suite_name,
                        "name": r.get("test_case") or r.get("attack_name") or "unknown",
                        "note": r.get("note") or r.get("description") or "",
                        "snippet": r.get("response_snippet", "")[:200],
                    })
    return failures


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def generate_markdown(data: Dict, agent_name: str) -> str:
    scores = _extract_scores(data)
    overall = _overall_score(scores)
    grade = _grade(overall)
    label = _grade_label(grade)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    failures = _collect_failures(data)

    lines = []
    lines.append("# Agent Reliability Audit Report")
    lines.append("")
    lines.append(f"**Agent:** {agent_name}  ")
    lines.append(f"**Generated:** {now}  ")
    if "endpoint" in data:
        lines.append(f"**Endpoint:** {data['endpoint']}  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Overall score
    grade_emoji = {"A": "✅", "B": "✅", "C": "⚠️", "D": "⚠️", "F": "❌"}.get(grade, "❓")
    lines.append("## Overall Reliability Score")
    lines.append("")
    lines.append(f"| Score | Grade | Status |")
    lines.append(f"|-------|-------|--------|")
    lines.append(f"| **{overall}/100** | **{grade}** | {grade_emoji} {label} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-mode table
    lines.append("## Failure Mode Scores")
    lines.append("")
    lines.append("| Failure Mode | Description | Score | Status |")
    lines.append("|-------------|-------------|-------|--------|")

    failing_modes = []
    for mode_key, mode_info in FAILURE_MODES.items():
        score = scores.get(mode_key)
        if score is None:
            score_str = "N/A"
            status = "—"
        else:
            score_str = f"{score:.1f}/100"
            if score >= 80:
                status = "✅ Good"
            elif score >= 60:
                status = "⚠️ Concerning"
            else:
                status = "❌ Critical"
                failing_modes.append(mode_key)

        lines.append(
            f"| {mode_info['name']} | {mode_info['description']} | {score_str} | {status} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Failed test cases
    if failures:
        lines.append("## Failed Tests")
        lines.append("")
        for f in failures[:30]:  # cap at 30 to keep report readable
            lines.append(f"- **[{f['suite']}]** {f['name']}")
            if f["note"]:
                lines.append(f"  - {f['note']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    if not failing_modes:
        lines.append("No critical failure modes detected. Agent demonstrates good overall reliability.")
    else:
        for mode_key in failing_modes:
            mode_info = FAILURE_MODES[mode_key]
            recs = RECOMMENDATIONS.get(mode_key, [])
            lines.append(f"### {mode_info['name']}")
            lines.append(f"*{mode_info['description']}*")
            lines.append("")
            for rec in recs:
                lines.append(f"- {rec}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by [Harper Labs Agent Reliability Toolkit](https://tylerdh12.github.io/agent-reliability-toolkit)*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

_CSS = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #0f1117;
  color: #e2e8f0;
  margin: 0;
  padding: 0;
}
.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
}
header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem 0 1rem;
  border-bottom: 1px solid #2d3748;
  margin-bottom: 2rem;
}
.logo {
  font-size: 1.5rem;
  font-weight: 800;
  color: #f6ad55;
  letter-spacing: -0.5px;
}
.logo span { color: #63b3ed; }
h1 { font-size: 1.6rem; font-weight: 700; margin: 0 0 0.25rem; }
h2 { font-size: 1.2rem; font-weight: 600; color: #90cdf4; margin: 2rem 0 0.75rem; border-bottom: 1px solid #2d3748; padding-bottom: 0.4rem; }
h3 { font-size: 1rem; font-weight: 600; color: #fbd38d; margin: 1rem 0 0.4rem; }
.meta { color: #718096; font-size: 0.85rem; margin-bottom: 1.5rem; }
.score-card {
  background: #1a202c;
  border: 1px solid #2d3748;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  margin-bottom: 2rem;
}
.score-big { font-size: 3.5rem; font-weight: 900; line-height: 1; }
.grade-big { font-size: 2rem; font-weight: 700; margin-top: 0.25rem; }
.grade-label { font-size: 1rem; color: #a0aec0; margin-top: 0.5rem; }
.good  { color: #68d391; }
.warn  { color: #fbd38d; }
.bad   { color: #fc8181; }
.na    { color: #718096; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}
th {
  background: #1a202c;
  color: #90cdf4;
  text-align: left;
  padding: 0.6rem 0.8rem;
  font-weight: 600;
  border-bottom: 1px solid #2d3748;
}
td {
  padding: 0.55rem 0.8rem;
  border-bottom: 1px solid #1a202c;
  vertical-align: top;
}
tr:nth-child(even) td { background: #161b27; }
.score-good { color: #68d391; font-weight: 700; }
.score-warn { color: #fbd38d; font-weight: 700; }
.score-bad  { color: #fc8181; font-weight: 700; }
.score-na   { color: #718096; }
.failure-list { list-style: none; padding: 0; }
.failure-list li {
  background: #1a202c;
  border-left: 3px solid #fc8181;
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.4rem;
  border-radius: 0 6px 6px 0;
  font-size: 0.88rem;
}
.failure-list li .suite { color: #90cdf4; font-weight: 600; }
.rec-block {
  background: #1a202c;
  border: 1px solid #2d3748;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
}
.rec-block ul { margin: 0.4rem 0 0; padding-left: 1.2rem; font-size: 0.9rem; color: #cbd5e0; }
footer {
  margin-top: 3rem;
  padding-top: 1rem;
  border-top: 1px solid #2d3748;
  text-align: center;
  font-size: 0.8rem;
  color: #4a5568;
}
footer a { color: #63b3ed; text-decoration: none; }
"""


def generate_html(data: Dict, agent_name: str) -> str:
    scores = _extract_scores(data)
    overall = _overall_score(scores)
    grade = _grade(overall)
    label = _grade_label(grade)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    failures = _collect_failures(data)

    grade_color = "good" if grade in ("A", "B") else ("warn" if grade in ("C", "D") else "bad")

    # Build scores table rows
    table_rows = []
    failing_modes = []
    for mode_key, mode_info in FAILURE_MODES.items():
        score = scores.get(mode_key)
        css = _score_color(score)
        if score is None:
            score_str = "N/A"
            status_str = '<span class="score-na">—</span>'
        else:
            score_str = f"{score:.1f}/100"
            if score >= 80:
                status_str = '<span class="score-good">✅ Good</span>'
            elif score >= 60:
                status_str = '<span class="score-warn">⚠️ Concerning</span>'
            else:
                status_str = '<span class="score-bad">❌ Critical</span>'
                failing_modes.append(mode_key)

        table_rows.append(
            f"<tr>"
            f"<td><strong>{mode_info['name']}</strong></td>"
            f"<td style='color:#718096;font-size:.85em'>{mode_info['description']}</td>"
            f"<td class='{css}'>{score_str}</td>"
            f"<td>{status_str}</td>"
            f"</tr>"
        )

    # Failures
    failure_html = ""
    if failures:
        items = "".join(
            f"<li><span class='suite'>[{f['suite']}]</span> {f['name']}"
            + (f"<br><small style='color:#718096'>{f['note']}</small>" if f["note"] else "")
            + "</li>"
            for f in failures[:30]
        )
        failure_html = f"<h2>Failed Tests</h2><ul class='failure-list'>{items}</ul>"

    # Recommendations
    rec_html = ""
    if failing_modes:
        for mode_key in failing_modes:
            mode_info = FAILURE_MODES[mode_key]
            recs = RECOMMENDATIONS.get(mode_key, [])
            rec_items = "".join(f"<li>{r}</li>" for r in recs)
            rec_html += (
                f"<div class='rec-block'>"
                f"<h3>{mode_info['name']}</h3>"
                f"<em style='color:#718096;font-size:.85em'>{mode_info['description']}</em>"
                f"<ul>{rec_items}</ul>"
                f"</div>"
            )
    else:
        rec_html = "<p style='color:#68d391'>No critical failure modes detected. Agent demonstrates good overall reliability.</p>"

    endpoint_line = (
        f"<br>Endpoint: <code style='color:#63b3ed'>{data['endpoint']}</code>"
        if "endpoint" in data
        else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent Reliability Report — {agent_name}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <div class="logo">Harper<span>Labs</span></div>
      <div style="color:#718096;font-size:.8rem">Agent Reliability Toolkit</div>
    </div>
  </header>

  <h1>Agent Reliability Audit Report</h1>
  <div class="meta">
    Agent: <strong>{agent_name}</strong>{endpoint_line}<br>
    Generated: {now}
  </div>

  <div class="score-card">
    <div class="score-big {grade_color}">{overall}/100</div>
    <div class="grade-big {grade_color}">{grade}</div>
    <div class="grade-label">{label}</div>
  </div>

  <h2>Failure Mode Scores</h2>
  <table>
    <thead>
      <tr>
        <th>Failure Mode</th>
        <th>Description</th>
        <th>Score</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {''.join(table_rows)}
    </tbody>
  </table>

  {failure_html}

  <h2>Recommendations</h2>
  {rec_html}

  <footer>
    Generated by
    <a href="https://tylerdh12.github.io/agent-reliability-toolkit">
      Harper Labs Agent Reliability Toolkit
    </a>
    &mdash; MIT License
  </footer>
</div>
</body>
</html>
"""
    return html


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Harper Labs Audit Report Generator — Markdown + HTML from JSON results"
    )
    # Accept input as positional arg OR --input flag for backward compat
    parser.add_argument(
        "input_positional",
        nargs="?",
        default=None,
        help="Path to JSON audit results file (positional)",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Path to JSON audit results file (alternative to positional)",
    )
    parser.add_argument(
        "--agent",
        default=None,
        help="Agent name (inferred from JSON if not set)",
    )
    # --output: write a single file to an explicit path (format inferred from extension)
    parser.add_argument(
        "--output",
        default=None,
        help="Write a single output file to this path (format inferred from .html / .md extension)",
    )
    # Legacy flags still work
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write reports to (default: current dir)",
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="File name prefix (default: agent name + timestamp)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "html", "both"],
        default="both",
        help="Output format (default: both)",
    )

    args = parser.parse_args()

    # Resolve input path (positional takes priority over --input)
    input_path = args.input_positional or args.input
    if not input_path:
        parser.error("Provide a JSON input file as a positional argument or via --input")

    # Load input
    try:
        with open(input_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    agent_name = args.agent or data.get("agent") or "unknown-agent"
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    written = []

    # --output: single explicit output path
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        ext = out.suffix.lower()
        if ext == ".html":
            out.write_text(generate_html(data, agent_name), encoding="utf-8")
        elif ext in (".md", ".markdown"):
            out.write_text(generate_markdown(data, agent_name), encoding="utf-8")
        else:
            # Default to format flag
            if args.format in ("html", "both"):
                out.write_text(generate_html(data, agent_name), encoding="utf-8")
            else:
                out.write_text(generate_markdown(data, agent_name), encoding="utf-8")
        written.append(str(out))
    else:
        # Legacy output-dir / output-prefix behaviour
        prefix = args.output_prefix or f"{agent_name}-{ts}"
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if args.format in ("markdown", "both"):
            md = generate_markdown(data, agent_name)
            md_path = out_dir / f"{prefix}.md"
            md_path.write_text(md, encoding="utf-8")
            written.append(str(md_path))

        if args.format in ("html", "both"):
            html = generate_html(data, agent_name)
            html_path = out_dir / f"{prefix}.html"
            html_path.write_text(html, encoding="utf-8")
            written.append(str(html_path))

    for path in written:
        print(f"✓ Written: {path}")

    # Exit code based on overall score
    scores = _extract_scores(data)
    overall = _overall_score(scores)
    return 0 if overall >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())
