"""Rule-based probable cause (LLM_PROVIDER=none, the default). First matching rule wins, so
specific rules come before general ones. Each rule says what it saw, then what to check next."""

import re
from collections.abc import Callable
from dataclasses import dataclass

from triage_bot.schemas.alertmanager import Alert
from triage_bot.services.context import AlertContext, Analysis

type Matcher = Callable[[Alert, AlertContext], bool]


@dataclass(frozen=True)
class Rule:
    name: str
    matches: Matcher
    cause: str
    next_steps: list[str]


def _logs_match(pattern: str) -> Matcher:
    regex = re.compile(pattern, re.IGNORECASE)
    return lambda _, ctx: any(regex.search(entry.line) for entry in ctx.logs)


def _name_matches(pattern: str) -> Matcher:
    regex = re.compile(pattern, re.IGNORECASE)
    return lambda alert, _: bool(regex.search(alert.name))


RULES: list[Rule] = [
    Rule(
        "chaos-experiment",
        _logs_match(r"fault injected"),
        "The errors are injected on purpose: FAULT_INJECTION_RATE is set on this deployment "
        "(chaos experiment).",
        [
            "Check whether a chaos test or canary with fault injection is running.",
            "Set FAULT_INJECTION_RATE=0 (or abort the rollout) once the experiment is done.",
        ],
    ),
    Rule(
        "database",
        _logs_match(
            r"OperationalError|could not connect|connection refused|too many connections|"
            r"server closed the connection|readiness check failed.*database"
        ),
        "The application can't reach the database, or the database is refusing connections.",
        [
            "Check the RDS instance status, CPU and DatabaseConnections in CloudWatch.",
            "Check /readyz on the API pods: database should be 'ok'.",
            "If connections are exhausted, compare DB_POOL_SIZE x replicas with max_connections.",
        ],
    ),
    Rule(
        "out-of-memory",
        lambda alert, ctx: bool(re.search(r"OOM|Memory", alert.name, re.IGNORECASE))
        or any("OOMKilled" in entry.line for entry in ctx.logs),
        "A container ran out of memory (OOMKilled) or is close to its memory limit.",
        [
            "kubectl describe pod <pod>: look for 'Last State: Terminated, Reason: OOMKilled'.",
            "Compare container_memory_working_set_bytes with the memory limit in Grafana.",
            "Raise the limit or find the leak (the trend over days tells which).",
        ],
    ),
    Rule(
        "crash-loop",
        lambda alert, ctx: bool(re.search(r"CrashLoop|Restart", alert.name, re.IGNORECASE))
        or bool(ctx.restarts),
        "Pods are restarting: the process crashes on start-up, or the liveness probe fails.",
        [
            "kubectl logs <pod> --previous: the crash reason is in the last run's output.",
            "Check recent config/secret changes (a missing env var fails settings validation).",
        ],
    ),
    Rule(
        "queue",
        lambda alert, ctx: bool(re.search(r"DLQ|DeadLetter|Queue", alert.name, re.IGNORECASE))
        or any("will be retried" in entry.line for entry in ctx.logs),
        "Queue messages are failing and being retried; repeated failures land in the DLQ.",
        [
            "Read the match-scorer error logs: the exception shows why handling fails.",
            "Look at a message in the dead-letter queue to see if one bad job is the cause.",
            "After fixing, redrive the DLQ (SQS console: 'Start DLQ redrive').",
        ],
    ),
    Rule(
        "scout",
        _name_matches(r"Scout"),
        "job-scout runs are failing or stale: a job board changed, or egress/DNS is broken.",
        [
            "Check the last CronJob run: kubectl get jobs -n <ns> and its pod logs.",
            "Look for 'source failed' logs: one company's board slug may have changed.",
        ],
    ),
    Rule(
        "latency",
        _name_matches(r"Latency|Slow|P9[59]"),
        "Requests are slower than the SLO allows.",
        [
            "Was something deployed in the last hour? Compare canary vs stable in Grafana.",
            "Check database query time and connection pool waits.",
            "Check CPU throttling (container_cpu_cfs_throttled_periods_total).",
        ],
    ),
    Rule(
        "error-rate",
        _name_matches(r"Error|5xx|Availability|Budget|SLO"),
        "The 5xx error rate is burning the availability error budget.",
        [
            "Was something deployed recently? If so, abort/roll back the rollout first.",
            "Group the error logs by route to find the failing endpoint.",
        ],
    ),
]

FALLBACK = Rule(
    "unknown",
    lambda _a, _c: True,
    "No known pattern matched. Start from the error logs and the runbook below.",
    ["Open the alert's graph (link at the bottom) and the pod logs in Grafana."],
)


def analyze(alert: Alert, ctx: AlertContext) -> Analysis:
    rule = next((r for r in RULES if r.matches(alert, ctx)), FALLBACK)
    return Analysis(cause=rule.cause, next_steps=rule.next_steps, provider="rules", rule=rule.name)
