from __future__ import annotations

import json
from typing import Iterable, Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
)


def fetch_transcript(
    video_id: str,
    languages: Optional[Iterable[str]] = None,
    preserve_formatting: bool = False,
) -> tuple[str, Optional[dict]]:
    api = YouTubeTranscriptApi()
    try:
        transcript = api.fetch(
            video_id,
            languages=list(languages) if languages else None,
            preserve_formatting=preserve_formatting,
        )
    except TranscriptsDisabled:
        return "disabled", None
    except NoTranscriptFound:
        return "not_found", None
    except (IpBlocked, RequestBlocked):
        return "blocked", None
    return "ok", {
        "video_id": video_id,
        "language_code": transcript.language_code,
        "is_generated": transcript.is_generated,
        "snippets_json": json.dumps(transcript.to_raw_data(), ensure_ascii=True),
    }
