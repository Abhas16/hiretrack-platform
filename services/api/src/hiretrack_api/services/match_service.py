"""Review queue (human in the loop) and the match profile the scorer uses.

Approve = "I am applying": we create an APPLIED application and hand back the job URL. The
user submits on the company's own site; HireTrack never submits anything for them.
"""

import uuid

from prometheus_client import Counter

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import ConflictError, NotFoundError
from hiretrack_api.models import Application, Match, MatchProfile
from hiretrack_api.repositories.match_repository import MatchProfileRepository, MatchRepository
from hiretrack_api.schemas.application import ApplicationCreate
from hiretrack_api.schemas.match import MatchProfileUpdate
from hiretrack_api.services.application_service import ApplicationService
from hiretrack_common.clock import Clock, utcnow
from hiretrack_common.domain.enums import (
    ApplicationSource,
    ApplicationStatus,
    JobSource,
    MatchStatus,
)

MATCHES_APPROVED = Counter("matches_approved_total", "Review-queue matches the user applied to")
MATCHES_SKIPPED = Counter("matches_skipped_total", "Review-queue matches the user skipped")

SOURCE_FOR_JOB = {
    JobSource.GREENHOUSE: ApplicationSource.GREENHOUSE,
    JobSource.LEVER: ApplicationSource.LEVER,
    JobSource.ASHBY: ApplicationSource.ASHBY,
}


class MatchService:
    def __init__(
        self,
        matches: MatchRepository,
        profiles: MatchProfileRepository,
        applications: ApplicationService,
        uow: UnitOfWork,
        now: Clock = utcnow,
    ) -> None:
        self._matches = matches
        self._profiles = profiles
        self._applications = applications
        self._uow = uow
        self._now = now

    # ---- review queue ------------------------------------------------------------------
    def search(
        self,
        user_id: uuid.UUID,
        status: MatchStatus | None,
        min_score: int,
        page: int,
        page_size: int,
    ) -> tuple[list[Match], int]:
        return self._matches.search(user_id, status, min_score, (page - 1) * page_size, page_size)

    def get(self, user_id: uuid.UUID, match_id: uuid.UUID, for_update: bool = False) -> Match:
        match = self._matches.get(user_id, match_id, for_update)
        if match is None:
            raise NotFoundError("Match not found")
        return match

    def approve(self, user_id: uuid.UUID, match_id: uuid.UUID) -> tuple[Match, Application]:
        match = self.get(user_id, match_id, for_update=True)
        self._require_new(match)
        job = match.job
        application = self._applications.build(
            user_id,
            ApplicationCreate(
                company_name=job.company_name,
                role=job.title[:200],
                location=job.location[:200] if job.location else None,
                source=SOURCE_FOR_JOB[job.source],
                job_url=job.url,
                status=ApplicationStatus.APPLIED,
                resume_variant_id=match.suggested_resume_variant_id,
            ),
        )
        match.status = MatchStatus.APPROVED
        match.decided_at = self._now()
        match.application_id = application.id
        self._uow.commit()  # application + match change land together, or not at all
        MATCHES_APPROVED.inc()
        return match, application

    def skip(self, user_id: uuid.UUID, match_id: uuid.UUID) -> Match:
        match = self.get(user_id, match_id, for_update=True)
        self._require_new(match)
        match.status = MatchStatus.SKIPPED
        match.decided_at = self._now()
        self._uow.commit()
        MATCHES_SKIPPED.inc()
        return match

    @staticmethod
    def _require_new(match: Match) -> None:
        if match.status != MatchStatus.NEW:
            raise ConflictError(f"Match was already {match.status.lower()}")

    # ---- profile -----------------------------------------------------------------------
    def get_profile(self, user_id: uuid.UUID) -> MatchProfile | None:
        return self._profiles.get(user_id)

    def save_profile(self, user_id: uuid.UUID, data: MatchProfileUpdate) -> MatchProfile:
        """Create or replace (PUT semantics). New jobs are scored with it from now on."""
        profile = self._profiles.get(user_id)
        if profile is None:
            profile = MatchProfile(user_id=user_id)
            self._profiles.add(profile)
        for field, value in data.model_dump().items():
            setattr(profile, field, value)
        self._uow.commit()
        return profile
