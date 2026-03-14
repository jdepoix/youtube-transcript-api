from typing import Optional, Iterable

from aiohttp import ClientSession

from .proxies import ProxyConfig

from ._transcripts import TranscriptListFetcher, FetchedTranscript, TranscriptList

import asyncio

class YouTubeTranscriptApi:
    def __init__(
        self,
        http_client: Optional[ClientSession] = None,
        proxy_config: Optional[ProxyConfig] = None
    ):
        self._http_client = http_client
        self._proxy_config = proxy_config

    def fetch(
        self,
        video_id: str,
        languages: Iterable[str] = ("en",),
        preserve_formatting: bool = False,
    ) -> FetchedTranscript:

        return asyncio.run(self._fetch_async(
            video_id=video_id,
            languages=languages,
            preserve_formatting=preserve_formatting
        ))

    def list(self, video_id: str) -> TranscriptList:
        return asyncio.run(self._list_async(video_id=video_id))

    async def _list_async(self, video_id: str) -> TranscriptList:
        async with YouTubeTranscriptAsyncApi(
            http_client=self._http_client,
            proxy_config=self._proxy_config
        ) as api:
            return await api.list(video_id)


    async def _fetch_async(
        self, 
        video_id: str, 
        languages: Iterable[str] = ("en",),
        preserve_formatting: bool = False,
        ) -> FetchedTranscript:
        async with YouTubeTranscriptAsyncApi(
            http_client=self._http_client,
            proxy_config=self._proxy_config
        ) as api:
            return await api.fetch(
                video_id=video_id,
                languages=languages,
                preserve_formatting=preserve_formatting
            )

class YouTubeTranscriptAsyncApi:
    def __init__(
        self,
        proxy_config: Optional[ProxyConfig] = None,
        http_client: Optional[ClientSession] = None,
    ):
        self._owns_session = http_client is None
        self._http_client = http_client or ClientSession()

        self._http_client.headers.update({"Accept-Language": "en-US"})

        if proxy_config and proxy_config.prevent_keeping_connections_alive:
            self._http_client.headers.update({"Connection": "close"})

        self._fetcher = TranscriptListFetcher(
            self._http_client, proxy_config=proxy_config
        )

    async def close(self):
        if self._owns_session and not self._http_client.closed:
            await self._http_client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        return False

    async def fetch(
        self,
        video_id: str,
        languages: Iterable[str] = ("en",),
        preserve_formatting: bool = False,
    ) -> FetchedTranscript:
        transcript_list = await self.list(video_id)
        transcript = transcript_list.find_transcript(languages)
        return await transcript.fetch(preserve_formatting=preserve_formatting)

    async def list(
        self,
        video_id: str,
    ) -> TranscriptList:
        return await self._fetcher.fetch(video_id)