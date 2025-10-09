from typing import List, Dict, Iterable, Optional, Union, Any
from dataclasses import dataclass, asdict
from .proxies import ProxyConfig
from ._transcripts import (
    FetchedTranscript,
    TranscriptListFetcher,
)

import asyncio

@dataclass
class BulkFetchResults:
    video_id: str
    result: Union[FetchedTranscript, Dict[str, Any]]

    def to_raw_data(self):
        return asdict(self)


class AsyncTranscriptHandler:
    """
    An asynchronous handler for fetching YouTube transcripts concurrently.

    This class provides high-level methods for fetching transcripts for one
    or more YouTube videos while handling concurrency limits, exceptions, 
    and optional proxy configuration.

    Features:
        - Concurrency limiting with an asyncio.Semaphore.
        - Fetching single or multiple transcripts concurrently.
        - Built-in error handling with structured exception serialization.
        - Proxy configuration support (optional).

    Attributes:
        _fetcher (TranscriptListFetcherAsync): 
            The transcript fetcher responsible for retrieving transcript lists.
        _proxy_config (Optional[ProxyConfig]): 
            Proxy configuration used when making requests.
        _semaphore (asyncio.Semaphore): 
            Semaphore to limit the number of concurrent requests.

    Example:
        >>> handler = AsyncTranscriptHandler(fetcher, max_concurrent=5)
        >>> results = await handler.fetch_bulk(
        ...     ["video_id_1", "video_id_2"],
        ... )
        >>> for r in results:
        ...     print(r.video_id, r.result)

    Notes:
        - `fetch_bulk` will always return a list of results in the same order
          as the provided `video_ids`.
        - If an exception occurs during fetching, the exception is captured
          and serialized into a dictionary with `type` and `message`.
    """
    def __init__(
        self,
        fetcher: TranscriptListFetcher,
        proxy_config: Optional[ProxyConfig] = None,
        max_concurrent: int = 10,
    ):
        self._fetcher = fetcher
        self._proxy_config = proxy_config
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_single(
        self,
        video_id: str,
        languages: Iterable[str] = ("en",),
        preserve_formatting: bool = False,
    ) -> FetchedTranscript:
        """Fetch transcript for a single video"""
        async with self._semaphore:
            transcript_list = await self._fetcher.fetch(video_id)
            transcript = transcript_list.find_transcript(languages)
            return await transcript.fetch(preserve_formatting=preserve_formatting)

    async def fetch_bulk(
        self,
        video_ids: List[str],
        languages: Iterable[str] = ("en",),
        preserve_formatting: bool = False,
    ) -> List[BulkFetchResults]:
        """Fetch transcripts for multiple videos concurrently with error handling.
        Args:
            video_ids: List of YouTube video IDs.
            languages: Languages to try in order.
            preserve_formatting: Whether to preserve original transcript formatting.

        Returns:
            A list of FetchResult objects, one per video_id.
        """

        async def _safe_fetch(video_id: str) -> Union[FetchedTranscript, Exception]:
            try:
                return await self.fetch_single(
                    video_id,
                    languages=languages,
                    preserve_formatting=preserve_formatting,
                )
            except Exception as e:
                return e

        tasks = [_safe_fetch(video_id) for video_id in video_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return self._process_bulk_results(video_ids, results)

    def _serialize_exception(self, exc: BaseException) -> Dict[str, Any]:
        """Convert exception to serializable dict"""
        return {
            "type": exc.__class__.__name__,
            "message": str(exc),
            **getattr(exc, "__dict__", {}),
        }

    def _process_bulk_results(
        self,
        video_ids: List[str],
        results: List[Union[FetchedTranscript, Exception]],
    ) -> List[BulkFetchResults]:
        """Process bulk fetch results with error handling"""
        processed_results = []

        for video_id, result in zip(video_ids, results):
            if isinstance(result, Exception):
                processed_results.append(
                    BulkFetchResults(
                        video_id=video_id,
                        result=self._serialize_exception(result)
                    )
                )
            else:
                processed_results.append(
                    BulkFetchResults(
                        video_id=video_id,
                        result=result
                    )
                )

        return processed_results
