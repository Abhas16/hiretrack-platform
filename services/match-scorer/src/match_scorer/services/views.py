"""Plain data the scoring code works on, decoupled from the ORM (easy to build in tests)."""

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class JobView:
    id: uuid.UUID
    company_name: str
    title: str
    location: str | None
    is_remote: bool
    description: str


@dataclass(frozen=True)
class VariantView:
    id: uuid.UUID
    name: str
    tags: list[str]
    summary: str | None = None


@dataclass(frozen=True)
class ProfileView:
    user_id: uuid.UUID
    skills: dict[str, int]  # skill -> weight 1..5
    target_roles: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    remote_ok: bool = True
    years_experience: int = 0
    variants: list[VariantView] = field(default_factory=list)
