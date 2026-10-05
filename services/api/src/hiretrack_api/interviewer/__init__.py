"""Mock-interview question generation and answer evaluation.

Two interchangeable providers (selected by LLM_PROVIDER):
- rule_based: built-in question bank, scoring by key-point coverage (default, free, offline)
- anthropic:  Claude writes role-specific questions and grades answers

The service layer only talks to the `Interviewer` protocol in base.py.
"""
