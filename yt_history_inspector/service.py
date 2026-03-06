from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from googleapiclient.errors import HttpError

from .db import Database
from .relevance import hide_reason
from .timeline import build_timeline
import json as json_lib

from .takeout import (
    parse_comments_csv,
    parse_playlists_csv,
    parse_playlist_items_csv,
    parse_search_history,
    parse_subscriptions_csv,
    parse_takeout,
    parse_video_metadata_csv,
    parse_video_recordings_csv,
    parse_video_texts_csv,
)
from .transcripts import fetch_transcript
from .wordclouds import word_counts
from .youtube_client import OAuthConfig, YouTubeOAuthClient


class HistoryInspector:
    def __init__(
        self,
        db_path: str,
        client_secrets_path: str,
        history_playlist_id: str = "HL",
    ):
        self.db = Database(db_path)
        self.history_playlist_id = history_playlist_id
        self.youtube = YouTubeOAuthClient(OAuthConfig(client_secrets_path))

    def close(self) -> None:
        self.db.close()

    def get_authorization_url(self, redirect_uri: str) -> tuple[str, str]:
        return self.youtube.authorization_url(redirect_uri)

    def save_credentials(self, credentials_json: str) -> None:
        self.db.set_oauth_token("youtube", credentials_json)
        self.db.commit()

    def load_credentials(self) -> Optional[str]:
        return self.db.get_oauth_token("youtube")

    def exchange_code(self, redirect_uri: str, code: str) -> str:
        credentials = self.youtube.fetch_token(redirect_uri, code)
        return self.youtube.credentials_to_json(credentials)

    def _get_credentials(self):
        token_json = self.load_credentials()
        if not token_json:
            raise RuntimeError("OAuth token missing. Connect your account first.")
        return self.youtube.credentials_from_json(token_json)

    def sync_history(self, max_items: int = 200) -> dict:
        credentials = self._get_credentials()
        collected = 0
        next_token = None
        seen_ids: list[str] = []
        try:
            while collected < max_items:
                response = self.youtube.list_history_playlist_items(
                    credentials,
                    playlist_id=self.history_playlist_id,
                    max_results=min(50, max_items - collected),
                    page_token=next_token,
                )
                items = response.get("items", [])
                for item in items:
                    normalized = self.youtube.normalize_playlist_item(item)
                    video_id = normalized.get("video_id")
                    watched_at = normalized.get("watched_at")
                    if not video_id or not watched_at:
                        continue
                    seen_ids.append(video_id)
                    self.db.add_history(video_id, watched_at)
                collected += len(items)
                next_token = response.get("nextPageToken")
                if not next_token:
                    break
        except HttpError as exc:
            return {
                "synced": 0,
                "error": str(exc),
                "hint": (
                    "YouTube does not always expose watch history via API. "
                    "If this fails, consider a Google Takeout import in phase 2."
                ),
            }

        self._sync_video_metadata(seen_ids, credentials)
        self.db.commit()
        return {"synced": len(seen_ids), "error": None}

    def import_takeout(self, path: str, fetch_metadata: bool = False) -> dict:
        items = parse_takeout(path)
        for item in items:
            self.db.ensure_video(item["video_id"])
            if item.get("title") or item.get("channel_title") or item.get("channel_id"):
                self.db.upsert_video(
                    {
                        "video_id": item["video_id"],
                        "title": item.get("title") or "",
                        "channel_id": item.get("channel_id") or "",
                        "channel_title": item.get("channel_title") or "",
                        "published_at": None,
                        "duration_seconds": None,
                        "tags": None,
                        "view_count": None,
                    }
                )
            self.db.add_history(item["video_id"], item["watched_at"])
        metadata_synced = 0
        if fetch_metadata:
            token_json = self.load_credentials()
            if token_json:
                credentials = self.youtube.credentials_from_json(token_json)
                self._sync_video_metadata([item["video_id"] for item in items], credentials)
                metadata_synced = len(items)
        self.db.commit()
        return {
            "synced": len(items),
            "metadata_synced": metadata_synced,
            "error": None,
        }

    def import_takeout_bundle(self, root_path: str, fetch_metadata: bool = False) -> dict:
        from pathlib import Path

        root = Path(root_path)
        totals = {
            "watch_history": 0,
            "watch_history_enriched": 0,
            "search_history": 0,
            "subscriptions": 0,
            "comments": 0,
            "playlists": 0,
            "playlist_items": 0,
            "video_metadata": 0,
            "video_texts": 0,
            "video_recordings": 0,
        }

        if root.is_file():
            if root.name in {"Suchverlauf.html", "search-history.html"}:
                searches = parse_search_history(str(root))
                for item in searches:
                    self.db.add_search_history(
                        item["query"], item["searched_at"], item["raw_url"]
                    )
                self.db.commit()
                totals["search_history"] = len(searches)
                return totals
            return self.import_takeout(str(root), fetch_metadata=fetch_metadata)

        playlist_title_map = {}
        playlists_files = list(root.rglob("Playlists.csv"))
        for playlists_file in playlists_files:
            for playlist in parse_playlists_csv(str(playlists_file)):
                if not playlist.get("playlist_id"):
                    continue
                playlist_title_map[playlist.get("title") or ""] = playlist["playlist_id"]
                self.db.upsert_playlist(
                    playlist["playlist_id"],
                    playlist.get("title"),
                    playlist.get("description"),
                    playlist.get("language"),
                    playlist.get("created_at"),
                    playlist.get("updated_at"),
                    playlist.get("order_type"),
                    playlist.get("visibility"),
                    playlist.get("add_new_videos_first"),
                )
                totals["playlists"] += 1

        for path in root.rglob("Abos.csv"):
            for entry in parse_subscriptions_csv(str(path)):
                if not entry.get("channel_id"):
                    continue
                self.db.upsert_subscription(
                    entry["channel_id"],
                    entry.get("channel_url"),
                    entry.get("channel_title"),
                )
                totals["subscriptions"] += 1

        for path in root.rglob("Kommentare.csv"):
            for entry in parse_comments_csv(str(path)):
                if not entry.get("comment_id"):
                    continue
                self.db.upsert_comment(
                    entry["comment_id"],
                    entry.get("channel_id"),
                    entry.get("created_at"),
                    entry.get("price"),
                    entry.get("video_id"),
                    entry.get("comment_text"),
                )
                totals["comments"] += 1

        for path in root.rglob("Suchverlauf.html"):
            for entry in parse_search_history(str(path)):
                self.db.add_search_history(
                    entry["query"], entry["searched_at"], entry["raw_url"]
                )
                totals["search_history"] += 1

        for path in root.rglob("watch-history.json"):
            result = self.import_takeout(str(path), fetch_metadata=fetch_metadata)
            totals["watch_history"] += result["synced"]

        for path in root.rglob("watch-history.csv"):
            result = self.import_takeout(str(path), fetch_metadata=fetch_metadata)
            totals["watch_history"] += result["synced"]

        for path in root.rglob("watch-history.html"):
            result = self.import_takeout(str(path), fetch_metadata=fetch_metadata)
            totals["watch_history"] += result["synced"]
            totals["watch_history_enriched"] += result["synced"]

        for path in root.rglob("Wiedergabeverlauf.html"):
            result = self.import_takeout(str(path), fetch_metadata=fetch_metadata)
            totals["watch_history"] += result["synced"]
            totals["watch_history_enriched"] += result["synced"]

        for path in root.rglob("Playlists"):
            for playlist_file in path.rglob("*-Videos.csv"):
                playlist_title = playlist_file.stem.replace("-Videos", "")
                playlist_id = playlist_title_map.get(playlist_title)
                for entry in parse_playlist_items_csv(str(playlist_file)):
                    if not entry.get("video_id"):
                        continue
                    self.db.add_playlist_item(
                        playlist_id,
                        playlist_title,
                        entry["video_id"],
                        entry.get("added_at"),
                    )
                    totals["playlist_items"] += 1

        for path in root.rglob("Video-Metadaten"):
            videos_csv = path / "Videos.csv"
            if videos_csv.exists():
                for entry in parse_video_metadata_csv(str(videos_csv)):
                    if not entry.get("video_id"):
                        continue
                    self.db.ensure_video(entry["video_id"])
                    self.db.upsert_video_metadata(
                        {
                            "video_id": entry["video_id"],
                            "duration_ms": entry.get("duration_ms"),
                            "audio_language": entry.get("audio_language"),
                            "category": entry.get("category"),
                            "description": entry.get("description"),
                            "channel_id": entry.get("channel_id"),
                            "tags_json": json_lib.dumps(entry.get("tags", []), ensure_ascii=True),
                            "title": entry.get("title"),
                            "privacy": entry.get("privacy"),
                            "status": entry.get("status"),
                            "created_at": entry.get("created_at"),
                            "published_at": entry.get("published_at"),
                        }
                    )
                    totals["video_metadata"] += 1

            texts_csv = path / "Videotexte.csv"
            if texts_csv.exists():
                for entry in parse_video_texts_csv(str(texts_csv)):
                    if not entry.get("video_id"):
                        continue
                    self.db.upsert_video_texts(
                        entry["video_id"],
                        entry.get("created_at"),
                        entry.get("updated_at"),
                        entry.get("description_text"),
                        entry.get("title_text"),
                    )
                    totals["video_texts"] += 1

            recordings_csv = path / "Videoaufzeichnungen.csv"
            if recordings_csv.exists():
                for entry in parse_video_recordings_csv(str(recordings_csv)):
                    if not entry.get("video_id"):
                        continue
                    self.db.upsert_video_recording(
                        entry["video_id"],
                        entry.get("recorded_at"),
                        entry.get("latitude"),
                        entry.get("longitude"),
                        entry.get("altitude"),
                    )
                    totals["video_recordings"] += 1

        self.db.commit()
        return totals

    def _sync_video_metadata(self, video_ids: Iterable[str], credentials) -> None:
        unique_ids = list(dict.fromkeys(video_ids))
        for i in range(0, len(unique_ids), 50):
            batch = unique_ids[i : i + 50]
            if not batch:
                continue
            response = self.youtube.fetch_videos(credentials, batch)
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                content = item.get("contentDetails", {})
                statistics = item.get("statistics", {})
                duration = _parse_duration(content.get("duration"))
                self.db.upsert_video(
                    {
                        "video_id": item.get("id"),
                        "title": snippet.get("title") or "",
                        "channel_id": snippet.get("channelId") or "",
                        "channel_title": snippet.get("channelTitle") or "",
                        "published_at": _iso(snippet.get("publishedAt")),
                        "duration_seconds": duration,
                        "tags": json.dumps(snippet.get("tags", []), ensure_ascii=True),
                        "view_count": int(statistics.get("viewCount", 0))
                        if statistics.get("viewCount")
                        else None,
                    }
                )

    def hide_video(self, video_id: str, reason: Optional[str] = None) -> None:
        self.db.set_hidden(video_id, True, hide_reason(reason))
        self.db.commit()

    def show_video(self, video_id: str) -> None:
        self.db.set_hidden(video_id, False, None)
        self.db.commit()

    def timeline(
        self,
        page: int = 1,
        per_page: int = 50,
        include_hidden: bool = False,
        no_transcript: bool = False,
    ) -> dict:
        page = max(page, 1)
        per_page = max(min(per_page, 200), 10)
        offset = (page - 1) * per_page
        total = self.db.count_history(include_hidden=include_hidden, no_transcript=no_transcript)
        rows = list(
            self.db.fetch_history(
                per_page,
                offset,
                include_hidden=include_hidden,
                no_transcript=no_transcript,
            )
        )
        items = build_timeline(rows)
        total_pages = max((total + per_page - 1) // per_page, 1)
        return {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
        }

    def sync_transcripts(
        self,
        video_ids: Iterable[str],
        languages: Optional[Iterable[str]] = None,
    ) -> dict:
        enqueued = 0
        for video_id in video_ids:
            if self.db.has_transcript(video_id):
                continue
            self.db.upsert_transcript_job(
                video_id,
                status="queued",
                attempts=0,
                next_retry_at=None,
                last_error=None,
            )
            enqueued += 1
        self.db.commit()
        return {"queued": enqueued}

    def sync_transcripts_for_visible(self, limit: int = 200) -> dict:
        rows = list(self.db.fetch_visible_history(limit))
        video_ids = [row["video_id"] for row in rows]
        enqueue_result = self.sync_transcripts(video_ids)
        process_result = self.process_transcript_queue(limit=20)
        return {**enqueue_result, **process_result}

    def wordcloud_counts(self, limit: int = 200):
        rows = list(self.db.fetch_visible_history(limit))
        snippets: list[str] = []
        for row in rows:
            for transcript in self.db.fetch_transcripts(row["video_id"]):
                snippets.append(transcript["snippets_json"])
        return word_counts(snippets)

    def video_detail(self, video_id: str) -> dict:
        video = self.db.fetch_video(video_id)
        if not video:
            return {}
        transcripts = [
            {
                "language_code": row["language_code"],
                "is_generated": bool(row["is_generated"]),
                "snippets_json": row["snippets_json"],
                "transcript_text": _join_transcript_text(row["snippets_json"]),
            }
            for row in self.db.fetch_transcripts(video_id)
        ]
        payload = dict(video)
        payload["transcripts"] = transcripts
        return payload

    def process_transcript_queue(self, limit: int = 20) -> dict:
        synced = 0
        blocked = 0
        not_found = 0
        disabled = 0
        deferred = 0
        for row in self.db.fetch_due_transcript_jobs(limit):
            video_id = row["video_id"]
            status, transcript = fetch_transcript(
                video_id,
                languages=["de", "en"],
            )
            if status == "ok" and transcript:
                self.db.upsert_transcript(
                    transcript["video_id"],
                    transcript["language_code"],
                    transcript["is_generated"],
                    transcript["snippets_json"],
                )
                self.db.delete_transcript_job(video_id)
                synced += 1
                continue

            attempts = (row["attempts"] or 0) + 1
            if status == "blocked":
                blocked += 1
                delay = min(24, 2 ** min(attempts, 4))
                next_retry = datetime.now(timezone.utc) + timedelta(hours=delay)
                self.db.upsert_transcript_job(
                    video_id,
                    status="blocked",
                    attempts=attempts,
                    next_retry_at=next_retry.isoformat(),
                    last_error="blocked",
                )
                deferred += 1
            elif status == "not_found":
                not_found += 1
                self.db.upsert_transcript_job(
                    video_id,
                    status="not_found",
                    attempts=attempts,
                    next_retry_at=None,
                    last_error="not_found",
                )
            elif status == "disabled":
                disabled += 1
                self.db.upsert_transcript_job(
                    video_id,
                    status="disabled",
                    attempts=attempts,
                    next_retry_at=None,
                    last_error="disabled",
                )
            else:
                deferred += 1
                next_retry = datetime.now(timezone.utc) + timedelta(hours=2)
                self.db.upsert_transcript_job(
                    video_id,
                    status="error",
                    attempts=attempts,
                    next_retry_at=next_retry.isoformat(),
                    last_error=status,
                )

        self.db.commit()
        return {
            "synced": synced,
            "blocked": blocked,
            "not_found": not_found,
            "disabled": disabled,
            "deferred": deferred,
        }


def _iso(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()


def _parse_duration(duration: Optional[str]) -> Optional[int]:
    if not duration:
        return None
    hours = minutes = seconds = 0
    value = duration.replace("PT", "")
    number = ""
    for char in value:
        if char.isdigit():
            number += char
            continue
        if char == "H":
            hours = int(number)
        elif char == "M":
            minutes = int(number)
        elif char == "S":
            seconds = int(number)
        number = ""
    return hours * 3600 + minutes * 60 + seconds


def _join_transcript_text(snippets_json: str) -> str:
    try:
        snippets = json_lib.loads(snippets_json)
    except (TypeError, json_lib.JSONDecodeError):
        return ""
    parts = [snippet.get("text", "").strip() for snippet in snippets]
    return " ".join(part for part in parts if part)
