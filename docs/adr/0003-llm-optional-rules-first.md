# ADR 0003: LLM features are optional, with rules and templates as the default

**Status:** accepted

## Context
Three features could use an LLM: practice-interview grading, application kits and incident
triage. LLM calls cost money, add latency and can fail or refuse.

## Decision
`LLM_PROVIDER=none` (the default) uses deterministic code: a question bank with key-point
scoring, kit templates, and ordered cause rules. `LLM_PROVIDER=anthropic` swaps in Claude
behind the same interface, always wrapped in a **fallback** to the rule-based version, with
structured JSON output and prompts that treat user/job/log text as untrusted data.

## Consequences
- Every feature works offline, in CI and for free. Tests never call an LLM.
- An LLM outage degrades quality, never availability (`*_llm_fallbacks_total` is a metric).
