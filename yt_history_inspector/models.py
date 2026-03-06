from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Video:
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: Optional[datetime]
    duration_seconds: Optional[int]
    tags: Optional[str]
    view_count: Optional[int]


@dataclass(frozen=True)
class HistoryEntry:
    video_id: str
    watched_at: datetime


@dataclass(frozen=True)
class Transcript:
    video_id: str
    language_code: str
    is_generated: bool
    snippets_json: str
