import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from hiretrack_common.db.models import Job, Match, MatchProfile, ResumeVariant
from hiretrack_common.domain.enums import MatchStatus
from match_scorer.services.match_service import NewMatch
from match_scorer.services.views import JobView, ProfileView, VariantView


class MatchRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_job(self, job_id: uuid.UUID) -> JobView | None:
        job = self._session.get(Job, job_id)
        if job is None:
            return None
        return JobView(
            id=job.id,
            company_name=job.company_name,
            title=job.title,
            location=job.location,
            is_remote=job.is_remote,
            description=job.description,
        )

    def profiles_without_match(self, job_id: uuid.UUID) -> list[ProfileView]:
        """Active profiles that have no match for this job yet, each with its resume variants
        (two queries in total, not one per profile)."""
        already = select(Match.user_id).where(Match.job_id == job_id)
        profiles = list(
            self._session.scalars(
                select(MatchProfile).where(
                    MatchProfile.is_active.is_(True), MatchProfile.user_id.not_in(already)
                )
            )
        )
        if not profiles:
            return []
        variants: dict[uuid.UUID, list[VariantView]] = defaultdict(list)
        rows = self._session.scalars(
            select(ResumeVariant).where(ResumeVariant.user_id.in_([p.user_id for p in profiles]))
        )
        for v in rows:
            variants[v.user_id].append(VariantView(v.id, v.name, list(v.tags), v.summary))
        return [
            ProfileView(
                user_id=p.user_id,
                skills=dict(p.skills),
                target_roles=list(p.target_roles),
                locations=list(p.locations),
                remote_ok=p.remote_ok,
                years_experience=p.years_experience,
                variants=variants[p.user_id],
            )
            for p in profiles
        ]

    def insert_match(self, match: NewMatch) -> bool:
        """True if stored; False if this user already had a match for the job."""
        stmt = (
            insert(Match)
            .values(
                id=uuid.uuid4(),
                user_id=match.user_id,
                job_id=match.job_id,
                score=match.score,
                matched_skills=match.matched_skills,
                gaps=[g[:200] for g in match.gaps],
                suggested_resume_variant_id=match.suggested_resume_variant_id,
                cover_note=match.kit.cover_note,
                resume_bullets=match.kit.resume_bullets,
                kit_provider=match.kit.provider,
                status=MatchStatus.NEW,
            )
            .on_conflict_do_nothing(constraint="uq_matches_user_id_job_id")
            .returning(Match.id)
        )
        return self._session.execute(stmt).first() is not None
