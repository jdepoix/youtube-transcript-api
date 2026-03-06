from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable


def build_timeline(rows: Iterable[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        watched_at = datetime.fromisoformat(row["watched_at"])
        day = watched_at.date().isoformat()
        grouped[day].append(
            {
                "video_id": row["video_id"],
                "title": row["title"],
                "channel_title": row["channel_title"],
                "watched_at": row["watched_at"],
                "hidden": bool(row["hidden"]),
                "has_transcript": bool(row["transcript_count"]),
            }
        )
    return [
        {"date": day, "items": items}
        for day, items in sorted(grouped.items(), reverse=True)
    ]
