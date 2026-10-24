"""Application kit = a short cover note + 2-3 tailored resume bullets for one job.

TemplateKitWriter (default, free, deterministic) fills templates from the matched skills.
The kit is a DRAFT for the user to edit; it never claims experience the profile doesn't list.
"""

from dataclasses import dataclass
from typing import Protocol

from match_scorer.services.views import JobView, VariantView

TEMPLATE = "template"

# Bullet templates for common skills; others use GENERIC_BULLET.
BULLETS: dict[str, str] = {
    "kubernetes": "Deployed and operated containerised services on Kubernetes, with health "
    "probes, resource limits and rolling updates.",
    "terraform": "Provisioned cloud infrastructure as code with Terraform modules and remote "
    "state, reviewed through pull requests.",
    "aws": "Built and ran workloads on AWS (VPC, IAM, EKS/ECR, RDS) with least-privilege access.",
    "docker": "Wrote small, non-root multi-stage Docker images and kept them reproducible "
    "with pinned base images.",
    "ci/cd": "Automated build, test and deploy pipelines so every change ships the same way.",
    "github actions": "Built GitHub Actions workflows with path filters, caching and required "
    "checks that gate merges to main.",
    "prometheus": "Instrumented services with Prometheus metrics and wrote alerts based on "
    "SLOs rather than raw thresholds.",
    "grafana": "Built Grafana dashboards that show request rate, errors and latency per service.",
    "python": "Wrote Python services and tooling with tests, type checking and linting in CI.",
    "linux": "Administered Linux hosts: systemd services, networking and troubleshooting.",
    "argo cd": "Ran GitOps delivery with Argo CD, so the cluster state always matches Git.",
    "helm": "Packaged applications as Helm charts with per-environment values.",
    "bash": "Automated routine operations with defensive Bash scripts (set -euo pipefail).",
    "azure devops": "Built Azure DevOps pipelines with staged environments and approvals.",
    "devsecops": "Added security scanning (images, dependencies, IaC) to CI so issues fail "
    "the build early.",
}
GENERIC_BULLET = (
    "Used {skill} hands-on in projects, automating repeatable steps and documenting decisions."
)


@dataclass(frozen=True)
class Kit:
    cover_note: str
    resume_bullets: list[str]
    provider: str


@dataclass(frozen=True)
class KitRequest:
    job: JobView
    matched_skills: list[str]
    gaps: list[str]
    variant: VariantView | None


class KitWriterError(Exception):
    """The kit writer couldn't produce a kit (e.g. the LLM call failed)."""


class KitWriter(Protocol):
    def write(self, request: KitRequest) -> Kit: ...


class TemplateKitWriter:
    def write(self, request: KitRequest) -> Kit:
        job, skills = request.job, request.matched_skills
        if skills:
            strengths = _join(skills[:3])
            focus = f"I work hands-on with {strengths}"
        else:
            focus = "I'm building my DevOps skills through hands-on projects"
        variant = f", as my {request.variant.name} resume shows" if request.variant else ""
        cover_note = (
            f"Hi {job.company_name} team,\n\n"
            f"I'm applying for the {job.title} role. {focus}{variant}. "
            f"I'd welcome the chance to bring that to {job.company_name}, and I'm happy to "
            "walk you through my projects.\n\nThank you for your time."
        )
        bullets = [BULLETS.get(s, GENERIC_BULLET.format(skill=s)) for s in skills[:3]]
        if len(bullets) < 2:
            bullets.append("Kept systems observable and documented, with runbooks for on-call.")
        return Kit(cover_note=cover_note, resume_bullets=bullets[:3], provider=TEMPLATE)


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} and {items[-1]}"


class FallbackKitWriter:
    """Use the primary writer (LLM); on any KitWriterError use the template instead."""

    def __init__(self, primary: KitWriter, fallback: KitWriter) -> None:
        self._primary = primary
        self._fallback = fallback

    def write(self, request: KitRequest) -> Kit:
        try:
            return self._primary.write(request)
        except KitWriterError:
            return self._fallback.write(request)
