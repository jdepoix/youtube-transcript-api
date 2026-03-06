from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
]


@dataclass(frozen=True)
class OAuthConfig:
    client_secrets_path: str
    scopes: Iterable[str] = tuple(DEFAULT_SCOPES)


def _utc_iso(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).isoformat()


def _ensure_credentials(credentials: Credentials) -> Credentials:
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return credentials


class YouTubeOAuthClient:
    def __init__(self, config: OAuthConfig):
        self.config = config

    def authorization_url(self, redirect_uri: str) -> tuple[str, str]:
        flow = Flow.from_client_secrets_file(
            self.config.client_secrets_path,
            scopes=list(self.config.scopes),
            redirect_uri=redirect_uri,
        )
        url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return url, state

    def fetch_token(self, redirect_uri: str, code: str) -> Credentials:
        flow = Flow.from_client_secrets_file(
            self.config.client_secrets_path,
            scopes=list(self.config.scopes),
            redirect_uri=redirect_uri,
        )
        flow.fetch_token(code=code)
        return flow.credentials

    def build_service(self, credentials: Credentials):
        credentials = _ensure_credentials(credentials)
        return build("youtube", "v3", credentials=credentials)

    def list_history_playlist_items(
        self,
        credentials: Credentials,
        playlist_id: str,
        max_results: int = 50,
        page_token: Optional[str] = None,
    ) -> dict:
        service = self.build_service(credentials)
        request = service.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=max_results,
            pageToken=page_token,
        )
        return request.execute()

    def fetch_videos(
        self,
        credentials: Credentials,
        video_ids: Iterable[str],
    ) -> dict:
        service = self.build_service(credentials)
        request = service.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(video_ids),
            maxResults=50,
        )
        return request.execute()

    @staticmethod
    def credentials_from_json(token_json: str) -> Credentials:
        data = json.loads(token_json)
        return Credentials.from_authorized_user_info(data)

    @staticmethod
    def credentials_to_json(credentials: Credentials) -> str:
        return credentials.to_json()

    @staticmethod
    def normalize_playlist_item(item: dict) -> dict:
        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})
        return {
            "video_id": content.get("videoId"),
            "watched_at": _utc_iso(snippet.get("publishedAt")),
        }
