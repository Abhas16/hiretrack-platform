import anthropic

from match_scorer.core.config import ScorerSettings
from match_scorer.services.kit import FallbackKitWriter, KitWriter, TemplateKitWriter
from match_scorer.services.kit_anthropic import AnthropicKitWriter


def build_kit_writer(settings: ScorerSettings) -> KitWriter:
    template = TemplateKitWriter()
    if settings.llm_provider != "anthropic":
        return template
    key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
    client = anthropic.Anthropic(
        api_key=key,  # None -> the SDK reads ANTHROPIC_API_KEY from the environment
        timeout=settings.llm_timeout_seconds,
        max_retries=1,
    )
    llm = AnthropicKitWriter(client, settings.anthropic_model, settings.anthropic_effort)
    return FallbackKitWriter(llm, template)
