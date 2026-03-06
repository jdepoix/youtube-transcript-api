from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Iterable, Optional


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    channel_title TEXT NOT NULL,
    published_at TEXT,
    duration_seconds INTEGER,
    tags TEXT,
    view_count INTEGER
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    watched_at TEXT NOT NULL,
    UNIQUE(video_id, watched_at),
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    language_code TEXT NOT NULL,
    is_generated INTEGER NOT NULL,
    snippets_json TEXT NOT NULL,
    UNIQUE(video_id, language_code),
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS relevance (
    video_id TEXT PRIMARY KEY,
    hidden INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS oauth_tokens (
    provider TEXT PRIMARY KEY,
    token_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transcript_jobs (
    video_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    next_retry_at TEXT,
    last_error TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    searched_at TEXT NOT NULL,
    raw_url TEXT,
    UNIQUE(query, searched_at, raw_url)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    channel_id TEXT PRIMARY KEY,
    channel_url TEXT,
    channel_title TEXT
);

CREATE TABLE IF NOT EXISTS comments (
    comment_id TEXT PRIMARY KEY,
    channel_id TEXT,
    created_at TEXT,
    price TEXT,
    video_id TEXT,
    comment_text TEXT
);

CREATE TABLE IF NOT EXISTS playlists (
    playlist_id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    language TEXT,
    created_at TEXT,
    updated_at TEXT,
    order_type TEXT,
    visibility TEXT,
    add_new_videos_first INTEGER
);

CREATE TABLE IF NOT EXISTS playlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id TEXT,
    playlist_title TEXT,
    video_id TEXT NOT NULL,
    added_at TEXT,
    UNIQUE(playlist_id, playlist_title, video_id, added_at)
);

CREATE TABLE IF NOT EXISTS video_metadata (
    video_id TEXT PRIMARY KEY,
    duration_ms INTEGER,
    audio_language TEXT,
    category TEXT,
    description TEXT,
    channel_id TEXT,
    tags_json TEXT,
    title TEXT,
    privacy TEXT,
    status TEXT,
    created_at TEXT,
    published_at TEXT
);

CREATE TABLE IF NOT EXISTS video_texts (
    video_id TEXT PRIMARY KEY,
    created_at TEXT,
    updated_at TEXT,
    description_text TEXT,
    title_text TEXT
);

CREATE TABLE IF NOT EXISTS video_recordings (
    video_id TEXT PRIMARY KEY,
    recorded_at TEXT,
    latitude REAL,
    longitude REAL,
    altitude REAL
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: str):
        self.path = path
        # Flask runs handlers across threads; allow the shared connection.
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def upsert_video(self, payload: dict) -> None:
        self._conn.execute(
            """
            INSERT INTO videos (
                video_id,
                title,
                channel_id,
                channel_title,
                published_at,
                duration_seconds,
                tags,
                view_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                title=excluded.title,
                channel_id=excluded.channel_id,
                channel_title=excluded.channel_title,
                published_at=excluded.published_at,
                duration_seconds=excluded.duration_seconds,
                tags=excluded.tags,
                view_count=excluded.view_count
            """,
            (
                payload["video_id"],
                payload["title"],
                payload["channel_id"],
                payload["channel_title"],
                payload.get("published_at"),
                payload.get("duration_seconds"),
                payload.get("tags"),
                payload.get("view_count"),
            ),
        )

    def add_history(self, video_id: str, watched_at: str) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO history (video_id, watched_at)
            VALUES (?, ?)
            """,
            (video_id, watched_at),
        )

    def ensure_video(self, video_id: str) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO videos (
                video_id,
                title,
                channel_id,
                channel_title
            )
            VALUES (?, '', '', '')
            """,
            (video_id,),
        )

    def upsert_transcript(
        self, video_id: str, language_code: str, is_generated: bool, snippets_json: str
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO transcripts (video_id, language_code, is_generated, snippets_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(video_id, language_code) DO UPDATE SET
                is_generated=excluded.is_generated,
                snippets_json=excluded.snippets_json
            """,
            (video_id, language_code, 1 if is_generated else 0, snippets_json),
        )

    def set_hidden(self, video_id: str, hidden: bool, reason: Optional[str]) -> None:
        self._conn.execute(
            """
            INSERT INTO relevance (video_id, hidden, reason, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                hidden=excluded.hidden,
                reason=excluded.reason,
                updated_at=excluded.updated_at
            """,
            (video_id, 1 if hidden else 0, reason, utc_now()),
        )

    def set_oauth_token(self, provider: str, token_json: str) -> None:
        self._conn.execute(
            """
            INSERT INTO oauth_tokens (provider, token_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                token_json=excluded.token_json,
                updated_at=excluded.updated_at
            """,
            (provider, token_json, utc_now()),
        )

    def get_oauth_token(self, provider: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT token_json FROM oauth_tokens WHERE provider = ?",
            (provider,),
        ).fetchone()
        return row["token_json"] if row else None

    def fetch_history(
        self,
        limit: int = 500,
        offset: int = 0,
        include_hidden: bool = False,
        no_transcript: bool = False,
    ) -> Iterable[sqlite3.Row]:
        where = []
        params: list = []
        if not include_hidden:
            where.append("COALESCE(relevance.hidden, 0) = 0")
        if no_transcript:
            where.append("transcripts.video_id IS NULL")
        where_clause = "WHERE " + " AND ".join(where) if where else ""
        query = f"""
            SELECT
                history.video_id,
                history.watched_at,
                videos.title,
                videos.channel_title,
                COALESCE(relevance.hidden, 0) AS hidden,
                COUNT(transcripts.id) AS transcript_count
            FROM history
            JOIN videos ON history.video_id = videos.video_id
            LEFT JOIN relevance ON history.video_id = relevance.video_id
            LEFT JOIN transcripts ON history.video_id = transcripts.video_id
            {where_clause}
            GROUP BY history.video_id, history.watched_at
            ORDER BY history.watched_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        return self._conn.execute(query, params)

    def count_history(self, include_hidden: bool = False, no_transcript: bool = False) -> int:
        where = []
        params: list = []
        if not include_hidden:
            where.append("COALESCE(relevance.hidden, 0) = 0")
        if no_transcript:
            where.append("transcripts.video_id IS NULL")
        where_clause = "WHERE " + " AND ".join(where) if where else ""
        query = f"""
            SELECT COUNT(*) AS count
            FROM history
            LEFT JOIN relevance ON history.video_id = relevance.video_id
            LEFT JOIN transcripts ON history.video_id = transcripts.video_id
            {where_clause}
        """
        row = self._conn.execute(query, params).fetchone()
        return int(row["count"]) if row else 0

    def fetch_video(self, video_id: str) -> Optional[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT videos.*, relevance.hidden, relevance.reason
            FROM videos
            LEFT JOIN relevance ON videos.video_id = relevance.video_id
            WHERE videos.video_id = ?
            """,
            (video_id,),
        ).fetchone()

    def fetch_transcripts(self, video_id: str) -> Iterable[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT language_code, is_generated, snippets_json
            FROM transcripts
            WHERE video_id = ?
            """,
            (video_id,),
        )

    def has_transcript(self, video_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM transcripts WHERE video_id = ? LIMIT 1",
            (video_id,),
        ).fetchone()
        return row is not None

    def upsert_transcript_job(
        self,
        video_id: str,
        status: str,
        attempts: int,
        next_retry_at: Optional[str],
        last_error: Optional[str],
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO transcript_jobs (video_id, status, attempts, next_retry_at, last_error, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                status=excluded.status,
                attempts=excluded.attempts,
                next_retry_at=excluded.next_retry_at,
                last_error=excluded.last_error,
                updated_at=excluded.updated_at
            """,
            (video_id, status, attempts, next_retry_at, last_error, utc_now()),
        )

    def delete_transcript_job(self, video_id: str) -> None:
        self._conn.execute(
            "DELETE FROM transcript_jobs WHERE video_id = ?",
            (video_id,),
        )

    def fetch_due_transcript_jobs(self, limit: int = 20) -> Iterable[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT video_id, status, attempts, next_retry_at, last_error
            FROM transcript_jobs
            WHERE next_retry_at IS NULL OR next_retry_at <= ?
            ORDER BY attempts ASC, updated_at ASC
            LIMIT ?
            """,
            (utc_now(), limit),
        )

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def add_search_history(self, query: str, searched_at: str, raw_url: Optional[str]) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO search_history (query, searched_at, raw_url)
            VALUES (?, ?, ?)
            """,
            (query, searched_at, raw_url),
        )

    def upsert_subscription(self, channel_id: str, channel_url: Optional[str], channel_title: Optional[str]) -> None:
        self._conn.execute(
            """
            INSERT INTO subscriptions (channel_id, channel_url, channel_title)
            VALUES (?, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                channel_url=excluded.channel_url,
                channel_title=excluded.channel_title
            """,
            (channel_id, channel_url, channel_title),
        )

    def upsert_comment(
        self,
        comment_id: str,
        channel_id: Optional[str],
        created_at: Optional[str],
        price: Optional[str],
        video_id: Optional[str],
        comment_text: Optional[str],
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO comments (
                comment_id,
                channel_id,
                created_at,
                price,
                video_id,
                comment_text
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(comment_id) DO UPDATE SET
                channel_id=excluded.channel_id,
                created_at=excluded.created_at,
                price=excluded.price,
                video_id=excluded.video_id,
                comment_text=excluded.comment_text
            """,
            (comment_id, channel_id, created_at, price, video_id, comment_text),
        )

    def upsert_playlist(
        self,
        playlist_id: str,
        title: Optional[str],
        description: Optional[str],
        language: Optional[str],
        created_at: Optional[str],
        updated_at: Optional[str],
        order_type: Optional[str],
        visibility: Optional[str],
        add_new_videos_first: Optional[bool],
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO playlists (
                playlist_id,
                title,
                description,
                language,
                created_at,
                updated_at,
                order_type,
                visibility,
                add_new_videos_first
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(playlist_id) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                language=excluded.language,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                order_type=excluded.order_type,
                visibility=excluded.visibility,
                add_new_videos_first=excluded.add_new_videos_first
            """,
            (
                playlist_id,
                title,
                description,
                language,
                created_at,
                updated_at,
                order_type,
                visibility,
                1 if add_new_videos_first else 0,
            ),
        )

    def add_playlist_item(
        self,
        playlist_id: Optional[str],
        playlist_title: Optional[str],
        video_id: str,
        added_at: Optional[str],
    ) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO playlist_items (
                playlist_id,
                playlist_title,
                video_id,
                added_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (playlist_id, playlist_title, video_id, added_at),
        )

    def upsert_video_metadata(self, payload: dict) -> None:
        self._conn.execute(
            """
            INSERT INTO video_metadata (
                video_id,
                duration_ms,
                audio_language,
                category,
                description,
                channel_id,
                tags_json,
                title,
                privacy,
                status,
                created_at,
                published_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                duration_ms=excluded.duration_ms,
                audio_language=excluded.audio_language,
                category=excluded.category,
                description=excluded.description,
                channel_id=excluded.channel_id,
                tags_json=excluded.tags_json,
                title=excluded.title,
                privacy=excluded.privacy,
                status=excluded.status,
                created_at=excluded.created_at,
                published_at=excluded.published_at
            """,
            (
                payload.get("video_id"),
                payload.get("duration_ms"),
                payload.get("audio_language"),
                payload.get("category"),
                payload.get("description"),
                payload.get("channel_id"),
                payload.get("tags_json"),
                payload.get("title"),
                payload.get("privacy"),
                payload.get("status"),
                payload.get("created_at"),
                payload.get("published_at"),
            ),
        )

    def upsert_video_texts(
        self,
        video_id: str,
        created_at: Optional[str],
        updated_at: Optional[str],
        description_text: Optional[str],
        title_text: Optional[str],
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO video_texts (
                video_id,
                created_at,
                updated_at,
                description_text,
                title_text
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                description_text=excluded.description_text,
                title_text=excluded.title_text
            """,
            (video_id, created_at, updated_at, description_text, title_text),
        )

    def upsert_video_recording(
        self,
        video_id: str,
        recorded_at: Optional[str],
        latitude: Optional[float],
        longitude: Optional[float],
        altitude: Optional[float],
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO video_recordings (
                video_id,
                recorded_at,
                latitude,
                longitude,
                altitude
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                recorded_at=excluded.recorded_at,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                altitude=excluded.altitude
            """,
            (video_id, recorded_at, latitude, longitude, altitude),
        )
