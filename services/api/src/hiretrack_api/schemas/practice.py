import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from hiretrack_api.schemas.common import ReadModel, WriteModel
from hiretrack_common.domain.enums import PracticeStatus

MIN_QUESTIONS = 3
MAX_QUESTIONS = 8


class PracticeTopicRead(ReadModel):
    id: str
    label: str


class PracticeMetaRead(ReadModel):
    """What the start screen needs: which interviewer is active and the topic choices."""

    provider: str
    topics: list[PracticeTopicRead]
    min_questions: int = MIN_QUESTIONS
    max_questions: int = MAX_QUESTIONS


class PracticeSessionCreate(WriteModel):
    """Give a role, or an application to practise for (its role is used), or both."""

    role: str | None = Field(default=None, min_length=1, max_length=200)
    application_id: uuid.UUID | None = None
    topics: list[str] = Field(default_factory=list, max_length=10)  # empty -> guessed from role
    question_count: int = Field(default=5, ge=MIN_QUESTIONS, le=MAX_QUESTIONS)

    @model_validator(mode="after")
    def _role_or_application(self) -> "PracticeSessionCreate":
        if not self.role and not self.application_id:
            raise ValueError("Provide a role or an application_id")
        return self


class PracticeAnswerCreate(WriteModel):
    answer: str = Field(min_length=1, max_length=5000)


class PracticeTurnRead(ReadModel):
    position: int
    topic: str
    question: str
    answer: str | None
    score: int | None
    strengths: list[str]
    improvements: list[str]
    feedback: str | None
    key_points: list[str]
    evaluated_by: str | None
    answered_at: datetime | None

    @model_validator(mode="after")
    def _hide_key_points_until_answered(self) -> "PracticeTurnRead":
        if self.answer is None:
            self.key_points = []  # don't reveal the "model answer" before the user tries
        return self


class PracticeSessionSummary(ReadModel):
    id: uuid.UUID
    role: str
    topics: list[str]
    provider: str
    status: PracticeStatus
    question_count: int
    answered_count: int
    average_score: float | None
    created_at: datetime
    completed_at: datetime | None

    @model_validator(mode="before")
    @classmethod
    def _count_turns(cls, data: Any) -> Any:
        if hasattr(data, "turns"):  # built from the ORM object
            values = {name: getattr(data, name) for name in _SESSION_FIELDS}
            values["question_count"] = len(data.turns)
            values["answered_count"] = sum(1 for turn in data.turns if turn.answer is not None)
            values["turns"] = data.turns
            return values
        return data


_SESSION_FIELDS = (
    "id",
    "application_id",
    "role",
    "topics",
    "provider",
    "status",
    "average_score",
    "created_at",
    "completed_at",
)


class PracticeSessionRead(PracticeSessionSummary):
    application_id: uuid.UUID | None
    turns: list[PracticeTurnRead]
