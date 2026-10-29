"""Handle one queued job: score it for every active profile and store the good matches.

Idempotent, because the queue delivers at least once:
  - profiles that already have a match for this job are skipped (no second LLM call), and
  - the insert is ON CONFLICT DO NOTHING on (user_id, job_id), for two workers racing.
"""

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from hiretrack_common.skills import SkillTaxonomy
from match_scorer.metrics import MATCHES_CREATED
from match_scorer.services.kit import Kit, KitRequest, KitWriter
from match_scorer.services.resume_picker import pick_variant
from match_scorer.services.scoring import score_job
from match_scorer.services.views import JobView, ProfileView

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewMatch:
    user_id: uuid.UUID
    job_id: uuid.UUID
    score: int
    matched_skills: list[str]
    gaps: list[str]
    suggested_resume_variant_id: uuid.UUID | None
    kit: Kit


class MatchStore(Protocol):
    def get_job(self, job_id: uuid.UUID) -> JobView | None: ...
    def profiles_without_match(self, job_id: uuid.UUID) -> list[ProfileView]: ...
    def insert_match(self, match: NewMatch) -> bool: ...


class MatchService:
    def __init__(
        self,
        store: MatchStore,
        commit: Callable[[], None],
        release: Callable[[], None],
        taxonomy: SkillTaxonomy,
        kit_writer: KitWriter,
        min_score: int,
    ) -> None:
        self._store = store
        self._commit = commit
        self._release = release
        self._taxonomy = taxonomy
        self._kits = kit_writer
        self._min_score = min_score

    def process(self, job_id: uuid.UUID) -> int:
        """Returns how many matches were created."""
        job = self._store.get_job(job_id)
        if job is None:
            logger.warning("job not found, skipping", extra={"job_id": str(job_id)})
            return 0
        profiles = self._store.profiles_without_match(job_id)
        # Give the DB connection back before possibly slow LLM calls (see API's UnitOfWork).
        self._release()

        pending: list[NewMatch] = []
        for profile in profiles:
            result = score_job(job, profile, self._taxonomy)
            if result.score < self._min_score:
                continue
            variant = pick_variant(profile.variants, result.matched_skills)
            kit = self._kits.write(KitRequest(job, result.matched_skills, result.gaps, variant))
            pending.append(
                NewMatch(
                    user_id=profile.user_id,
                    job_id=job.id,
                    score=result.score,
                    matched_skills=result.matched_skills,
                    gaps=result.gaps,
                    suggested_resume_variant_id=variant.id if variant else None,
                    kit=kit,
                )
            )

        created = sum(1 for match in pending if self._store.insert_match(match))
        self._commit()
        MATCHES_CREATED.inc(created)
        logger.info(
            "job scored",
            extra={"job_id": str(job_id), "profiles": len(profiles), "matches_created": created},
        )
        return created
