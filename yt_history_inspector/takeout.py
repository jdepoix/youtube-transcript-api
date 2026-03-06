from __future__ import annotations

import csv
import json
import re
from html import unescape
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlparse


def _parse_video_id(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.hostname and "youtu" in parsed.hostname:
        if parsed.path.startswith("/watch"):
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/shorts/")[-1].split("?")[0]
        if parsed.hostname == "youtu.be":
            return parsed.path.strip("/") or None
    return None


def _parse_time(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None


def parse_takeout(path: str) -> list[dict]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(path)
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return _parse_json(file_path)
    if suffix == ".csv":
        return _parse_csv(file_path)
    if suffix == ".html":
        return _parse_html(file_path)
    raise ValueError("Unsupported Takeout format. Use JSON or CSV.")


def _parse_json(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("watch-history", [])
    results: list[dict] = []
    for item in items:
        video_id = _parse_video_id(item.get("titleUrl"))
        watched_at = _parse_time(item.get("time"))
        if not video_id or not watched_at:
            continue
        results.append({"video_id": video_id, "watched_at": watched_at})
    return results


def _parse_csv(path: Path) -> list[dict]:
    results: list[dict] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            video_id = _parse_video_id(row.get("titleUrl") or row.get("title_url"))
            watched_at = _parse_time(row.get("time") or row.get("watched_at"))
            if not video_id or not watched_at:
                continue
            results.append({"video_id": video_id, "watched_at": watched_at})
    return results


WATCH_RE = re.compile(
    r'<a href="(https?://www\.youtube\.com/watch\?v=[^"]+|https?://youtu\.be/[^"]+)">(.*?)</a>'
)
DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4}),\s*(\d{2}:\d{2}:\d{2})\s*(MEZ|MESZ)?")
SEARCH_RE = re.compile(
    r'Gesucht nach:\s*&nbsp;<a href="(https?://www\.youtube\.com/results\?search_query=[^"]+)">'
)
CHANNEL_RE = re.compile(r'<a href="(https?://www\.youtube\.com/channel/[^"]+)">([^<]+)</a>')


def _parse_html(path: Path) -> list[dict]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    results: list[dict] = []
    for match in WATCH_RE.finditer(html):
        url = match.group(1)
        title = unescape(match.group(2)).strip()
        video_id = _parse_video_id(url)
        if not video_id:
            continue
        tail = html[match.end() : match.end() + 400]
        date_match = DATE_RE.search(tail)
        if not date_match:
            continue
        channel_match = CHANNEL_RE.search(tail)
        channel_url = None
        channel_title = None
        if channel_match:
            channel_url = channel_match.group(1)
            channel_title = unescape(channel_match.group(2)).strip()
        channel_id = _parse_channel_id(channel_url)
        date_part, time_part, tz_label = date_match.groups()
        watched_at = _parse_de_datetime(date_part, time_part, tz_label)
        if not watched_at:
            continue
        results.append(
            {
                "video_id": video_id,
                "watched_at": watched_at,
                "title": title or None,
                "channel_id": channel_id,
                "channel_title": channel_title,
            }
        )
    return results


def parse_search_history(path: str) -> list[dict]:
    file_path = Path(path)
    html = file_path.read_text(encoding="utf-8", errors="ignore")
    results: list[dict] = []
    for match in SEARCH_RE.finditer(html):
        url = match.group(1)
        query = _parse_search_query(url)
        if not query:
            continue
        tail = html[match.end() : match.end() + 200]
        date_match = DATE_RE.search(tail)
        if not date_match:
            continue
        date_part, time_part, tz_label = date_match.groups()
        searched_at = _parse_de_datetime(date_part, time_part, tz_label)
        if not searched_at:
            continue
        results.append({"query": query, "searched_at": searched_at, "raw_url": url})
    return results


def _parse_search_query(url: str) -> str | None:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    values = params.get("search_query")
    if not values:
        return None
    return values[0].replace("+", " ").strip() or None


def _parse_channel_id(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.path.startswith("/channel/"):
        return parsed.path.split("/channel/")[-1].split("?")[0]
    return None


def parse_subscriptions_csv(path: str) -> list[dict]:
    file_path = Path(path)
    results: list[dict] = []
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            results.append(
                {
                    "channel_id": row.get("Kanal-ID") or row.get("Channel ID"),
                    "channel_url": row.get("Kanal-URL") or row.get("Channel URL"),
                    "channel_title": row.get("Kanaltitel") or row.get("Channel title"),
                }
            )
    return results


def parse_comments_csv(path: str) -> list[dict]:
    file_path = Path(path)
    results: list[dict] = []
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            results.append(
                {
                    "comment_id": row.get("Kommentar-ID") or row.get("Comment ID"),
                    "channel_id": row.get("Kanal-ID") or row.get("Channel ID"),
                    "created_at": row.get("Zeitstempel der Erstellung des Kommentars")
                    or row.get("Comment creation timestamp"),
                    "price": row.get("Preis") or row.get("Price"),
                    "video_id": row.get("Video-ID") or row.get("Video ID"),
                    "comment_text": row.get("Kommentartext") or row.get("Comment text"),
                }
            )
    return results


def parse_playlists_csv(path: str) -> list[dict]:
    file_path = Path(path)
    results: list[dict] = []
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            results.append(
                {
                    "playlist_id": row.get("Playlist-ID") or row.get("Playlist ID"),
                    "add_new_videos_first": _parse_bool(
                        row.get("Neue Videos oben hinzufügen")
                        or row.get("Add new videos to top")
                    ),
                    "description": row.get("Playlist-Beschreibung (Original)")
                    or row.get("Playlist description"),
                    "title": row.get("Playlist-Titel (Original)") or row.get("Playlist title"),
                    "language": row.get("Sprache des Playlist-Titels (Original)")
                    or row.get("Playlist title language"),
                    "created_at": row.get("Zeitstempel bei Playlist-Erstellung")
                    or row.get("Playlist creation timestamp"),
                    "updated_at": row.get("Zeitstempel bei Playlist-Update")
                    or row.get("Playlist update timestamp"),
                    "order_type": row.get("Videoreihenfolge der Playlist")
                    or row.get("Playlist video order"),
                    "visibility": row.get("Playlist-Sichtbarkeit") or row.get("Playlist visibility"),
                }
            )
    return results


def parse_playlist_items_csv(path: str) -> list[dict]:
    file_path = Path(path)
    results: list[dict] = []
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            results.append(
                {
                    "video_id": row.get("Video-ID") or row.get("Video ID"),
                    "added_at": row.get("Zeitstempel bei Erstellung des Playlist-Videos")
                    or row.get("Playlist video creation timestamp"),
                }
            )
    return results


def parse_video_metadata_csv(path: str) -> list[dict]:
    file_path = Path(path)
    results: list[dict] = []
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            tags = [value for key, value in row.items() if key.startswith("Tag:") and value]
            results.append(
                {
                    "video_id": row.get("Video-ID") or row.get("Video ID"),
                    "duration_ms": _parse_int(row.get("Ungefähre Dauer (ms)") or row.get("Approximate duration (ms)")),
                    "audio_language": row.get("Audiosprache des Videos") or row.get("Audio language"),
                    "category": row.get("Videokategorie") or row.get("Video category"),
                    "description": row.get("Videobeschreibung (Original)") or row.get("Video description"),
                    "channel_id": row.get("Kanal-ID") or row.get("Channel ID"),
                    "tags": tags,
                    "title": row.get("Videotitel (Original)") or row.get("Video title"),
                    "privacy": row.get("Datenschutz") or row.get("Privacy"),
                    "status": row.get("Videostatus") or row.get("Status"),
                    "created_at": row.get("Zeitstempel bei Videoerstellung") or row.get("Video creation timestamp"),
                    "published_at": row.get("Zeitstempel bei Videoveröffentlichung") or row.get("Video publish timestamp"),
                }
            )
    return results


def parse_video_texts_csv(path: str) -> list[dict]:
    file_path = Path(path)
    results: list[dict] = []
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            results.append(
                {
                    "video_id": row.get("Video-ID") or row.get("Video ID"),
                    "created_at": row.get("Videotext – Zeitstempel erstellen")
                    or row.get("Video text creation timestamp"),
                    "description_text": row.get("Videobeschreibung – Textabschnitte 1")
                    or row.get("Video description text section 1"),
                    "title_text": row.get("Videotitel – Textabschnitte 1")
                    or row.get("Video title text section 1"),
                    "updated_at": row.get("Videotext – Zeitstempel aktualisieren")
                    or row.get("Video text update timestamp"),
                }
            )
    return results


def parse_video_recordings_csv(path: str) -> list[dict]:
    file_path = Path(path)
    results: list[dict] = []
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            results.append(
                {
                    "video_id": row.get("Video-ID") or row.get("Video ID"),
                    "recorded_at": row.get("Videoaufnahme – Datum") or row.get("Recording date"),
                    "altitude": _parse_float(row.get("Videoaufnahme – Höhe") or row.get("Recording altitude")),
                    "latitude": _parse_float(row.get("Videoaufnahme – Breitengrad") or row.get("Recording latitude")),
                    "longitude": _parse_float(row.get("Videoaufnahme – Längengrad") or row.get("Recording longitude")),
                }
            )
    return results


def _parse_bool(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    return normalized in {"wahr", "true", "yes", "ja", "1"}


def _parse_int(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def _parse_float(value: str | None) -> float | None:
    try:
        return float(value) if value else None
    except ValueError:
        return None


def _parse_de_datetime(date_part: str, time_part: str, tz_label: str | None) -> str | None:
    try:
        day, month, year = date_part.split(".")
        iso = f"{year}-{month}-{day}T{time_part}"
        dt = datetime.fromisoformat(iso)
        if tz_label == "MESZ":
            dt = dt.replace(tzinfo=timezone(timedelta(hours=2)))
        elif tz_label == "MEZ":
            dt = dt.replace(tzinfo=timezone(timedelta(hours=1)))
        return dt.isoformat()
    except ValueError:
        return None
