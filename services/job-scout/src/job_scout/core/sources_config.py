"""Reads config/sources.yaml (which companies to check, on which job board)."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from hiretrack_common.domain.enums import JobSource

BOARDS: dict[str, JobSource] = {
    "greenhouse": JobSource.GREENHOUSE,
    "lever": JobSource.LEVER,
    "ashby": JobSource.ASHBY,
}


class SourceConfig(BaseModel):
    board: Literal["greenhouse", "lever", "ashby"]
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9._-]+$")
    company: str = Field(min_length=1, max_length=200)
    keywords: list[str] | None = None  # None = use defaults.keywords

    @property
    def job_source(self) -> JobSource:
        return BOARDS[self.board]


class _Defaults(BaseModel):
    keywords: list[str] = Field(default_factory=list)


class SourcesFile(BaseModel):
    defaults: _Defaults = Field(default_factory=_Defaults)
    sources: list[SourceConfig]

    def keywords_for(self, source: SourceConfig) -> list[str]:
        words = source.keywords if source.keywords is not None else self.defaults.keywords
        return [w.lower() for w in words]


def load_sources(path: Path) -> SourcesFile:
    return SourcesFile.model_validate(yaml.safe_load(path.read_text("utf-8")))
