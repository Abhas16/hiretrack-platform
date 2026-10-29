"""Suggest the resume variant whose tags overlap most with the job's matched skills."""

from match_scorer.services.views import VariantView


def pick_variant(variants: list[VariantView], matched_skills: list[str]) -> VariantView | None:
    wanted = {s.lower() for s in matched_skills}
    best: VariantView | None = None
    best_overlap = 0
    for variant in sorted(variants, key=lambda v: v.name.lower()):  # ties -> alphabetical
        overlap = len(wanted & {t.lower() for t in variant.tags})
        if overlap > best_overlap:
            best, best_overlap = variant, overlap
    return best  # None when no variant shares a single skill
