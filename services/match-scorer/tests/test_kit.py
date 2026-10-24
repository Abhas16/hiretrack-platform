from match_scorer.services.kit import (
    FallbackKitWriter,
    Kit,
    KitRequest,
    KitWriterError,
    TemplateKitWriter,
)
from match_scorer.services.views import VariantView

from .conftest import make_job


def request(skills: list[str], variant: VariantView | None = None) -> KitRequest:
    return KitRequest(make_job(title="Platform Engineer"), skills, [], variant)


def test_template_kit_mentions_company_role_and_top_skills() -> None:
    kit = TemplateKitWriter().write(request(["kubernetes", "terraform", "aws", "python"]))
    assert kit.provider == "template"
    assert "Acme" in kit.cover_note and "Platform Engineer" in kit.cover_note
    assert "kubernetes, terraform and aws" in kit.cover_note
    assert len(kit.resume_bullets) == 3
    assert "Terraform" in kit.resume_bullets[1]


def test_template_kit_always_has_two_bullets() -> None:
    kit = TemplateKitWriter().write(request(["pulumi"]))
    assert len(kit.resume_bullets) == 2
    assert "pulumi" in kit.resume_bullets[0]


def test_template_kit_names_the_variant() -> None:
    variant = VariantView(id=make_job().id, name="DevOps - Kubernetes", tags=[])
    kit = TemplateKitWriter().write(request(["kubernetes"], variant))
    assert "DevOps - Kubernetes resume" in kit.cover_note


class BrokenWriter:
    def write(self, request: KitRequest) -> Kit:
        raise KitWriterError("api down")


def test_fallback_uses_template_when_llm_fails() -> None:
    kit = FallbackKitWriter(BrokenWriter(), TemplateKitWriter()).write(request(["aws"]))
    assert kit.provider == "template"
