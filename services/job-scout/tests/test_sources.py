"""Each board adapter turns its API's JSON into the same JobPosting shape."""

from collections.abc import Callable
from datetime import UTC, datetime

from hiretrack_common.domain.enums import JobSource
from job_scout.sources import PoliteHttpClient, build_boards

from .conftest import Router, boards_router

MakeHttp = Callable[[Router], PoliteHttpClient]


def test_greenhouse_normalizes_and_unescapes_html(make_http: MakeHttp) -> None:
    board = build_boards(make_http(boards_router), 20_000)[JobSource.GREENHOUSE]
    jobs = board.fetch("examplecorp", "Example Corp")

    assert len(jobs) == 2
    sre = jobs[0]
    assert sre.external_id == "7712345"
    assert sre.title == "Senior Site Reliability Engineer, Platform"
    assert sre.location == "Remote, India"
    assert sre.is_remote is True
    assert sre.url == "https://boards.greenhouse.io/examplecorp/jobs/7712345"
    assert "<" not in sre.description  # tags stripped, entities decoded
    assert "Kubernetes fleet on AWS" in sre.description
    assert "5+ years of experience" in sre.description
    assert sre.posted_at == datetime(2026, 10, 9, 14, 0, tzinfo=UTC)


def test_lever_joins_description_lists(make_http: MakeHttp) -> None:
    [job] = build_boards(make_http(boards_router), 20_000)[JobSource.LEVER].fetch(
        "examplelever", "Example Lever"
    )
    assert job.title == "DevOps Engineer"
    assert job.location == "Pune"
    assert job.is_remote is False  # hybrid
    assert "Requirements" in job.description
    assert "2+ years with Docker and Kubernetes" in job.description
    assert job.posted_at is not None and job.posted_at.tzinfo is not None


def test_ashby_skips_unlisted_jobs(make_http: MakeHttp) -> None:
    jobs = build_boards(make_http(boards_router), 20_000)[JobSource.ASHBY].fetch(
        "exampleashby", "Example Ashby"
    )
    assert [j.title for j in jobs] == ["Platform Engineer (Cloud Infrastructure)"]
    assert jobs[0].is_remote is True


def test_dedupe_hash_ignores_text_changes(make_http: MakeHttp) -> None:
    board = build_boards(make_http(boards_router), 20_000)[JobSource.GREENHOUSE]
    first = board.fetch("examplecorp", "Example Corp")[0]
    renamed = board.fetch("ExampleCorp", "Renamed Inc")[0]
    assert first.dedupe_hash == renamed.dedupe_hash  # same board + slug + job ID
    assert len(first.dedupe_hash) == 64


def test_description_is_truncated(make_http: MakeHttp) -> None:
    board = build_boards(make_http(boards_router), 1000)[JobSource.LEVER]
    [job] = board.fetch("examplelever", "Example Lever")
    assert len(job.description) <= 1000
