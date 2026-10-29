"""The skill taxonomy (config/skills.yaml): canonical skill names, aliases and gap weights.

Used by match-scorer to find skills in job adverts, and by the API to offer skill names.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

DEFAULT_GAP_WEIGHT = 2


class _SkillEntry(BaseModel):
    aliases: list[str] = Field(default_factory=list)
    weight: int = Field(default=DEFAULT_GAP_WEIGHT, ge=1, le=5)


class _TaxonomyFile(BaseModel):
    skills: dict[str, _SkillEntry]


def _phrase_pattern(phrases: list[str]) -> re.Pattern[str]:
    # Whole-word match. Plain \b fails on phrases like "ci/cd" or "node.js", so use explicit
    # "not a word character" lookarounds instead. Longest first: "github actions" before "git".
    alternatives = "|".join(re.escape(p) for p in sorted(phrases, key=len, reverse=True))
    return re.compile(rf"(?<![\w])(?:{alternatives})(?![\w])", re.IGNORECASE)


@dataclass(frozen=True)
class Skill:
    name: str
    weight: int
    pattern: re.Pattern[str]


class SkillTaxonomy:
    def __init__(self, skills: dict[str, tuple[list[str], int]]) -> None:
        self._skills = {
            name.lower(): Skill(
                name=name.lower(),
                weight=weight,
                pattern=_phrase_pattern([name, *aliases]),
            )
            for name, (aliases, weight) in skills.items()
        }

    @classmethod
    def load(cls, path: str | Path) -> "SkillTaxonomy":
        data = _TaxonomyFile.model_validate(yaml.safe_load(Path(path).read_text("utf-8")))
        return cls({name: (e.aliases, e.weight) for name, e in data.skills.items()})

    @property
    def names(self) -> list[str]:
        return sorted(self._skills)

    def weight(self, name: str) -> int:
        skill = self._skills.get(name.lower())
        return skill.weight if skill else DEFAULT_GAP_WEIGHT

    def extract(self, text: str) -> set[str]:
        """Canonical names of every taxonomy skill mentioned in the text."""
        return {skill.name for skill in self._skills.values() if skill.pattern.search(text)}

    def mentions(self, name: str, text: str) -> bool:
        """Is this skill in the text? Skills missing from the taxonomy match their own name."""
        skill = self._skills.get(name.lower())
        pattern = skill.pattern if skill else _phrase_pattern([name])
        return pattern.search(text) is not None
