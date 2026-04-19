"""Shared data models for multi-source aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    GITHUB = "github"
    NPM = "npm"
    PYPI = "pypi"
    HACKERNEWS = "hackernews"
    REDDIT = "reddit"
    VSCODE = "vscode"
    TWITTER = "twitter"
    YOUTUBE = "youtube"


@dataclass
class SourceResult:
    source: SourceType
    fetched_at: datetime
    records: list[dict[str, object]]
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.records) > 0 or len(self.errors) == 0

    @property
    def record_count(self) -> int:
        return len(self.records)
