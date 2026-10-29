"""Render the GitHub issue (Markdown). Everything from the system (labels, logs) is treated
as untrusted text: escaped in tables, fenced in code blocks, so it can't break the layout or
@-mention people."""

from datetime import datetime

from triage_bot.schemas.alertmanager import Alert
from triage_bot.services.context import AlertContext, Analysis

FENCE = "```"


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("@", "@\u200b")


def _when(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M UTC")


def runbook_url(alert: Alert, base_url: str) -> str | None:
    if alert.annotations.get("runbook_url"):
        return alert.annotations["runbook_url"]
    if base_url:
        return f"{base_url.rstrip('/')}/{alert.name}.md"
    return None


def issue_title(alert: Alert) -> str:
    summary = alert.annotations.get("summary", "").replace("\n", " ").strip()
    title = f"[{alert.severity.upper()}] {alert.name}" + (f": {summary}" if summary else "")
    return title[:240]


def issue_body(alert: Alert, ctx: AlertContext, analysis: Analysis, runbook: str | None) -> str:
    parts = [
        f"## {alert.name} is firing",
        "",
        "| | |",
        "|---|---|",
        f"| Severity | **{_cell(alert.severity)}** |",
        f"| Started | {_when(alert.starts_at)} |",
        f"| Window analysed | {_when(ctx.window_start)} to {_when(ctx.window_end)} |",
        "| Labels | "
        + " ".join(f"`{_cell(k)}={_cell(v)}`" for k, v in sorted(alert.labels.items()))
        + " |",
        "",
    ]
    for key in ("summary", "description"):
        if alert.annotations.get(key):
            parts.append(f"**{key.title()}:** {_cell(alert.annotations[key])}")
    parts += ["", f"### Probable cause ({analysis.provider})", "", analysis.cause, ""]
    parts += ["**Next steps**", *[f"- {step}" for step in analysis.next_steps], ""]

    if ctx.restarts:
        parts += ["### Affected pods", "", "| Pod | Restarts in window |", "|---|---|"]
        parts += [f"| `{_cell(r.pod)}` | {r.restarts:.0f} |" for r in ctx.restarts]
        parts.append("")

    if ctx.series:
        parts += ["### Metric snapshot", "", f"`{_cell(ctx.query)}`", ""]
        parts += ["| Series | Last | Min | Max |", "|---|---|---|---|"]
        for s in ctx.series:
            name = ", ".join(f"{k}={v}" for k, v in sorted(s.labels.items())) or "(value)"
            parts.append(f"| {_cell(name)} | {s.last:.4g} | {s.minimum:.4g} | {s.maximum:.4g} |")
        parts.append("")

    parts += [f"### Error logs (latest {len(ctx.logs)})", ""]
    if ctx.logs:
        lines = [f"{e.timestamp:%H:%M:%S} {e.pod}: {e.line}" for e in ctx.logs]
        parts += [f"{FENCE}text", *(line.replace(FENCE, "'''") for line in lines), FENCE]
    else:
        parts.append("No error-level logs in the window.")
    parts.append("")

    if ctx.problems:
        parts += ["### Missing context", "", *[f"- {_cell(p)}" for p in ctx.problems], ""]

    links = [f"[Runbook]({runbook})"] if runbook else []
    if alert.generator_url:
        links.append(f"[Alert graph]({alert.generator_url})")
    parts += [
        "---",
        " · ".join([*links, f"Fingerprint `{alert.fingerprint}`", "filed by triage-bot"]),
    ]
    return "\n".join(parts)


def resolved_comment(alert: Alert) -> str:
    ended = _when(alert.ends_at) if alert.ends_at else "just now"
    return (
        f"Resolved: **{alert.name}** stopped firing at {ended}. Left open for the follow-up "
        "(cause, fix, prevention); close it when done."
    )
