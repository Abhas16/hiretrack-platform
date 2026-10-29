from hiretrack_common.domain.enums import JobSource
from job_scout.sources.ashby import AshbyBoard
from job_scout.sources.base import FetchError, JobBoard, JobPosting
from job_scout.sources.greenhouse import GreenhouseBoard
from job_scout.sources.http import PoliteHttpClient
from job_scout.sources.lever import LeverBoard


def build_boards(http: PoliteHttpClient, max_description_chars: int) -> dict[JobSource, JobBoard]:
    """One adapter per job board, all behind the same JobBoard interface."""
    return {
        JobSource.GREENHOUSE: GreenhouseBoard(http, max_description_chars),
        JobSource.LEVER: LeverBoard(http, max_description_chars),
        JobSource.ASHBY: AshbyBoard(http, max_description_chars),
    }


__all__ = ["FetchError", "JobBoard", "JobPosting", "PoliteHttpClient", "build_boards"]
