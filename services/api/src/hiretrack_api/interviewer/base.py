from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Question:
    topic: str
    text: str
    key_points: list[str]  # what a strong answer covers
    provider: str = ""  # which interviewer actually wrote it (matters after a fallback)


@dataclass(frozen=True)
class Evaluation:
    score: int  # 0..10
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    feedback: str = ""
    provider: str = ""


class InterviewerError(Exception):
    """A provider could not produce questions or an evaluation (network, refusal, bad output)."""


class Interviewer(Protocol):
    name: str

    def generate_questions(self, role: str, topics: list[str], count: int) -> list[Question]: ...

    def evaluate(self, role: str, question: Question, answer: str) -> Evaluation: ...
