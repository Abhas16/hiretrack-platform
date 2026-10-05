"""Rule-based interviewer: built-in question bank, and scoring by key-point coverage.

Free, offline and deterministic. It can't judge nuance like an LLM, but it reliably tells you
which key ideas your answer mentioned and which it missed.
"""

import random
import re
from functools import lru_cache
from importlib import resources

import yaml

from hiretrack_api.interviewer.base import Evaluation, Question

NAME = "rule_based"
MIN_WORDS = 12  # shorter answers are capped: interviewers expect a few sentences
_PREFIX = 4  # crude stemming: "restarts" and "restart" both become "rest"
_WORD = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    [
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "such",
        "into",
        "your",
        "you",
        "are",
        "can",
        "how",
        "what",
        "when",
        "why",
        "does",
        "should",
        "its",
        "their",
        "them",
        "then",
        "than",
        "only",
        "also",
        "each",
        "over",
        "under",
        "like",
        "about",
        "must",
        "use",
        "uses",
        "using",
    ]
)


@lru_cache
def load_bank() -> dict[str, list[dict[str, object]]]:
    text = (
        resources.files("hiretrack_api.interviewer")
        .joinpath("question_bank.yaml")
        .read_text(encoding="utf-8")
    )
    bank: dict[str, list[dict[str, object]]] = yaml.safe_load(text)
    return bank


def terms(text: str) -> set[str]:
    return {
        word[:_PREFIX]
        for word in _WORD.findall(text.lower())
        if len(word) >= 3 and word not in _STOPWORDS
    }


def covers(answer_terms: set[str], key_point: str) -> bool:
    """A key point counts as covered when the answer uses at least half of its key terms."""
    point_terms = terms(key_point)
    return bool(point_terms) and len(point_terms & answer_terms) / len(point_terms) >= 0.5


class RuleBasedInterviewer:
    name = NAME

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()  # noqa: S311 - picking questions, not cryptography

    def generate_questions(self, role: str, topics: list[str], count: int) -> list[Question]:
        bank = load_bank()
        pools = {topic: list(bank.get(topic, [])) for topic in topics}
        for pool in pools.values():
            self._rng.shuffle(pool)

        questions: list[Question] = []
        # Round-robin over topics so a 5-question session covers 5 different areas.
        while len(questions) < count and any(pools.values()):
            for topic in topics:
                if pools[topic] and len(questions) < count:
                    item = pools[topic].pop()
                    key_points = [str(point) for point in item["key_points"]]  # type: ignore[attr-defined]
                    questions.append(
                        Question(topic, str(item["question"]), key_points, provider=NAME)
                    )
        return questions

    def evaluate(self, role: str, question: Question, answer: str) -> Evaluation:
        answer_terms = terms(answer)
        covered = [point for point in question.key_points if covers(answer_terms, point)]
        missed = [point for point in question.key_points if point not in covered]

        score = round(10 * len(covered) / len(question.key_points)) if question.key_points else 0
        improvements = [f"Mention: {point}" for point in missed]
        if len(answer.split()) < MIN_WORDS:
            score = min(score, 4)
            improvements.append("Give a fuller answer: 3-5 sentences, ideally with an example.")

        return Evaluation(
            score=score,
            strengths=[f"Covered: {point}" for point in covered],
            improvements=improvements,
            feedback=_summary(score, len(covered), len(question.key_points)),
            provider=NAME,
        )


def _summary(score: int, covered: int, total: int) -> str:
    coverage = f"You covered {covered} of {total} key points."
    if score >= 8:
        return f"Strong answer. {coverage}"
    if score >= 5:
        return f"Good start. {coverage} Add the missing points to make it complete."
    return f"{coverage} Review the key points below and try explaining them in your own words."
