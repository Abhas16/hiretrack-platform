import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from hiretrack_api.models import Match, MatchProfile
from hiretrack_common.domain.enums import MatchStatus


class MatchRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _select(user_id: uuid.UUID) -> Select[tuple[Match]]:
        return (
            select(Match)
            .options(joinedload(Match.job), joinedload(Match.suggested_resume_variant))
            .where(Match.user_id == user_id)
        )

    def search(
        self,
        user_id: uuid.UUID,
        status: MatchStatus | None,
        min_score: int,
        offset: int,
        limit: int,
    ) -> tuple[list[Match], int]:
        conditions = [Match.user_id == user_id, Match.score >= min_score]
        if status:
            conditions.append(Match.status == status)
        total = self._session.scalar(select(func.count()).select_from(Match).where(*conditions))
        stmt = (
            self._select(user_id)
            .where(*conditions)
            .order_by(Match.score.desc(), Match.created_at.desc(), Match.id)
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.scalars(stmt)), total or 0

    def get(
        self, user_id: uuid.UUID, match_id: uuid.UUID, for_update: bool = False
    ) -> Match | None:
        stmt = self._select(user_id).where(Match.id == match_id)
        if for_update:
            # Lock the row until commit: two clicks on "Approve" can't create two applications.
            stmt = stmt.with_for_update(of=Match)
        return self._session.scalar(stmt)


class MatchProfileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: uuid.UUID) -> MatchProfile | None:
        return self._session.scalar(select(MatchProfile).where(MatchProfile.user_id == user_id))

    def add(self, profile: MatchProfile) -> None:
        self._session.add(profile)
        self._session.flush()
