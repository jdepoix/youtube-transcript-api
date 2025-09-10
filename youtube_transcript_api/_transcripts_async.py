from httpx import AsyncClient, Response, HTTPError
from typing import List, Dict, Iterator, Iterable, Pattern, Optional, Union, Any
from ._settings import WATCH_URL, INNERTUBE_CONTEXT, INNERTUBE_API_URL
from dataclasses import dataclass, asdict
from .proxies import ProxyConfig
from ._transcripts import (
    FetchedTranscript,
    FetchedTranscriptSnippet,
    _TranslationLanguage,
    _PlayabilityStatus,
    _PlayabilityFailedReason,
)
from ._errors import (
    VideoUnavailable,
    YouTubeRequestFailed,
    NoTranscriptFound,
    TranscriptsDisabled,
    NotTranslatable,
    TranslationLanguageNotAvailable,
    FailedToCreateConsentCookie,
    InvalidVideoId,
    IpBlocked,
    RequestBlocked,
    AgeRestricted,
    VideoUnplayable,
    YouTubeDataUnparsable,
    PoTokenRequired,
)

from html import unescape

from defusedxml import ElementTree

import re

import asyncio

from itertools import chain


def _raise_http_errors(response: Response, video_id: str) -> Response:
    try:
        if response.status_code == 429:
            raise IpBlocked(video_id)
        response.raise_for_status()
        return response
    except HTTPError as error:
        raise YouTubeRequestFailed(video_id, error)


class TranscriptAsync:
    def __init__(
        self,
        http_client: AsyncClient,
        video_id: str,
        url: str,
        language: str,
        language_code: str,
        is_generated: bool,
        translation_languages: List[_TranslationLanguage],
    ):
        """
        You probably don't want to initialize this directly. Usually you'll access Transcript objects using a
        TranscriptList.
        """
        self._http_client = http_client
        self.video_id = video_id
        self._url = url
        self.language = language
        self.language_code = language_code
        self.is_generated = is_generated
        self.translation_languages = translation_languages
        self._translation_languages_dict = {
            translation_language.language_code: translation_language.language
            for translation_language in translation_languages
        }

    async def fetch(self, preserve_formatting: bool = False) -> FetchedTranscript:
        """
        Loads the actual transcript data.
        :param preserve_formatting: whether to keep select HTML text formatting
        """
        if "&exp=xpe" in self._url:
            raise PoTokenRequired(self.video_id)
        response = await self._http_client.get(self._url)
        transcript_parser = _TranscriptParserAsync(
            preserve_formatting=preserve_formatting
        )
        snippets = transcript_parser.parse(
            _raise_http_errors(response, self.video_id).text,
        )

        return FetchedTranscript(
            snippets=snippets,
            video_id=self.video_id,
            language=self.language,
            language_code=self.language_code,
            is_generated=self.is_generated,
        )

    def __str__(self) -> str:
        return '{language_code} ("{language}"){translation_description}'.format(
            language=self.language,
            language_code=self.language_code,
            translation_description="[TRANSLATABLE]" if self.is_translatable else "",
        )

    @property
    def is_translatable(self) -> bool:
        return len(self.translation_languages) > 0

    def translate(self, language_code: str) -> "TranscriptAsync":
        if not self.is_translatable:
            raise NotTranslatable(self.video_id)

        if language_code not in self._translation_languages_dict:
            raise TranslationLanguageNotAvailable(self.video_id)

        return TranscriptAsync(
            self._http_client,
            self.video_id,
            "{url}&tlang={language_code}".format(
                url=self._url, language_code=language_code
            ),
            self._translation_languages_dict[language_code],
            language_code,
            True,
            [],
        )


class TranscriptListAsync:
    """
    This object represents a list of transcripts. It can be iterated over to list all transcripts which are available
    for a given YouTube video. Also, it provides functionality to search for a transcript in a given language.
    """

    def __init__(
        self,
        video_id: str,
        manually_created_transcripts: Dict[str, TranscriptAsync],
        generated_transcripts: Dict[str, TranscriptAsync],
        translation_languages: List[_TranslationLanguage],
    ):
        """
        The constructor is only for internal use. Use the static build method instead.

        :param video_id: the id of the video this TranscriptList is for
        :param manually_created_transcripts: dict mapping language codes to the manually created transcripts
        :param generated_transcripts: dict mapping language codes to the generated transcripts
        :param translation_languages: list of languages which can be used for translatable languages
        """
        self.video_id = video_id
        self._manually_created_transcripts = manually_created_transcripts
        self._generated_transcripts = generated_transcripts
        self._translation_languages = translation_languages

    @staticmethod
    def build(
        http_client: AsyncClient, video_id: str, captions_json: Dict
    ) -> "TranscriptListAsync":
        """
        Factory method for TranscriptList.

        :param http_client: http client which is used to make the transcript retrieving http calls
        :param video_id: the id of the video this TranscriptList is for
        :param captions_json: the JSON parsed from the YouTube pages static HTML
        :return: the created TranscriptList
        """
        translation_languages = [
            _TranslationLanguage(
                language=translation_language["languageName"]["runs"][0]["text"],
                language_code=translation_language["languageCode"],
            )
            for translation_language in captions_json.get("translationLanguages", [])
        ]

        manually_created_transcripts = {}
        generated_transcripts = {}

        for caption in captions_json["captionTracks"]:
            if caption.get("kind", "") == "asr":
                transcript_dict = generated_transcripts
            else:
                transcript_dict = manually_created_transcripts

            transcript_dict[caption["languageCode"]] = TranscriptAsync(
                http_client,
                video_id,
                caption["baseUrl"].replace("&fmt=srv3", ""),
                caption["name"]["runs"][0]["text"],
                caption["languageCode"],
                caption.get("kind", "") == "asr",
                translation_languages if caption.get("isTranslatable", False) else [],
            )

        return TranscriptListAsync(
            video_id,
            manually_created_transcripts,
            generated_transcripts,
            translation_languages,
        )

    def __iter__(self) -> Iterator[TranscriptAsync]:
        return chain(
            self._manually_created_transcripts.values(),
            self._generated_transcripts.values(),
        )

    def find_transcript(self, language_codes: Iterable[str]) -> TranscriptAsync:
        """
        Finds a transcript for a given language code. Manually created transcripts are returned first and only if none
        are found, generated transcripts are used. If you only want generated transcripts use
        `find_manually_created_transcript` instead.

        :param language_codes: A list of language codes in a descending priority. For example, if this is set to
        ['de', 'en'] it will first try to fetch the german transcript (de) and then fetch the english transcript (en) if
        it fails to do so.
        :return: the found Transcript
        """
        return self._find_transcript(
            language_codes,
            [self._manually_created_transcripts, self._generated_transcripts],
        )

    def find_generated_transcript(
        self, language_codes: Iterable[str]
    ) -> TranscriptAsync:
        """
        Finds an automatically generated transcript for a given language code.

        :param language_codes: A list of language codes in a descending priority. For example, if this is set to
        ['de', 'en'] it will first try to fetch the german transcript (de) and then fetch the english transcript (en) if
        it fails to do so.
        :return: the found Transcript
        """
        return self._find_transcript(language_codes, [self._generated_transcripts])

    def find_manually_created_transcript(
        self, language_codes: Iterable[str]
    ) -> TranscriptAsync:
        """
        Finds a manually created transcript for a given language code.

        :param language_codes: A list of language codes in a descending priority. For example, if this is set to
        ['de', 'en'] it will first try to fetch the german transcript (de) and then fetch the english transcript (en) if
        it fails to do so.
        :return: the found Transcript
        """
        return self._find_transcript(
            language_codes, [self._manually_created_transcripts]
        )

    def _find_transcript(
        self,
        language_codes: Iterable[str],
        transcript_dicts: List[Dict[str, TranscriptAsync]],
    ) -> TranscriptAsync:
        for language_code in language_codes:
            for transcript_dict in transcript_dicts:
                if language_code in transcript_dict:
                    return transcript_dict[language_code]

        raise NoTranscriptFound(self.video_id, language_codes, self)

    def __str__(self) -> str:
        return (
            "For this video ({video_id}) transcripts are available in the following languages:\n\n"
            "(MANUALLY CREATED)\n"
            "{available_manually_created_transcript_languages}\n\n"
            "(GENERATED)\n"
            "{available_generated_transcripts}\n\n"
            "(TRANSLATION LANGUAGES)\n"
            "{available_translation_languages}"
        ).format(
            video_id=self.video_id,
            available_manually_created_transcript_languages=self._get_language_description(
                str(transcript)
                for transcript in self._manually_created_transcripts.values()
            ),
            available_generated_transcripts=self._get_language_description(
                str(transcript) for transcript in self._generated_transcripts.values()
            ),
            available_translation_languages=self._get_language_description(
                '{language_code} ("{language}")'.format(
                    language=translation_language.language,
                    language_code=translation_language.language_code,
                )
                for translation_language in self._translation_languages
            ),
        )

    def _get_language_description(self, transcript_strings: Iterable[str]) -> str:
        description = "\n".join(
            " - {transcript}".format(transcript=transcript)
            for transcript in transcript_strings
        )
        return description if description else "None"


class TranscriptListFetcherAsync:
    def __init__(self, http_client: AsyncClient, proxy_config: Optional[ProxyConfig]):
        self._http_client = http_client
        self._proxy_config = proxy_config

    async def fetch(self, video_id: str) -> TranscriptListAsync:
        return TranscriptListAsync.build(
            self._http_client,
            video_id,
            await self._fetch_captions_json(video_id),
        )

    async def _fetch_captions_json(self, video_id: str, try_number: int = 0) -> Dict:
        try:
            html = await self._fetch_video_html(video_id)
            api_key = self._extract_innertube_api_key(html, video_id)
            innertube_data = await self._fetch_innertube_data(video_id, api_key)
            return self._extract_captions_json(innertube_data, video_id)
        except RequestBlocked as exception:
            retries = (
                0
                if self._proxy_config is None
                else self._proxy_config.retries_when_blocked
            )
            if try_number + 1 < retries:
                return await self._fetch_captions_json(
                    video_id, try_number=try_number + 1
                )
            raise exception.with_proxy_config(self._proxy_config)

    def _extract_innertube_api_key(self, html: str, video_id: str) -> str:
        pattern = r'"INNERTUBE_API_KEY":\s*"([a-zA-Z0-9_-]+)"'
        match = re.search(pattern, html)
        if match and len(match.groups()) == 1:
            return match.group(1)
        if 'class="g-recaptcha"' in html:
            raise IpBlocked(video_id)
        raise YouTubeDataUnparsable(video_id)  # pragma: no cover

    def _extract_captions_json(self, innertube_data: Dict, video_id: str) -> Dict:
        self._assert_playability(innertube_data.get("playabilityStatus"), video_id)

        captions_json = innertube_data.get("captions", {}).get(
            "playerCaptionsTracklistRenderer"
        )
        if captions_json is None or "captionTracks" not in captions_json:
            raise TranscriptsDisabled(video_id)

        return captions_json

    def _assert_playability(self, playability_status_data: Dict, video_id: str) -> None:
        playability_status = playability_status_data.get("status")
        if (
            playability_status != _PlayabilityStatus.OK.value
            and playability_status is not None
        ):
            reason = playability_status_data.get("reason")
            if playability_status == _PlayabilityStatus.LOGIN_REQUIRED.value:
                if reason == _PlayabilityFailedReason.BOT_DETECTED.value:
                    raise RequestBlocked(video_id)
                if reason == _PlayabilityFailedReason.AGE_RESTRICTED.value:
                    raise AgeRestricted(video_id)
            if (
                playability_status == _PlayabilityStatus.ERROR.value
                and reason == _PlayabilityFailedReason.VIDEO_UNAVAILABLE.value
            ):
                if video_id.startswith("http://") or video_id.startswith("https://"):
                    raise InvalidVideoId(video_id)
                raise VideoUnavailable(video_id)
            subreasons = (
                playability_status_data.get("errorScreen", {})
                .get("playerErrorMessageRenderer", {})
                .get("subreason", {})
                .get("runs", [])
            )
            raise VideoUnplayable(
                video_id, reason, [run.get("text", "") for run in subreasons]
            )

    def _create_consent_cookie(self, html: str, video_id: str) -> None:
        match = re.search('name="v" value="(.*?)"', html)
        if match is None:
            raise FailedToCreateConsentCookie(video_id)
        self._http_client.cookies.set(
            "CONSENT", "YES+" + match.group(1), domain=".youtube.com"
        )

    async def _fetch_video_html(self, video_id: str) -> str:
        html = await self._fetch_html(video_id)
        if 'action="https://consent.youtube.com/s"' in html:
            self._create_consent_cookie(html, video_id)
            html = await self._fetch_html(video_id)
            if 'action="https://consent.youtube.com/s"' in html:
                raise FailedToCreateConsentCookie(video_id)
        return html

    async def _fetch_html(self, video_id: str) -> str:
        response = await self._http_client.get(WATCH_URL.format(video_id=video_id))
        return unescape(_raise_http_errors(response, video_id).text)

    async def _fetch_innertube_data(self, video_id: str, api_key: str) -> Dict:
        response = await self._http_client.post(
            INNERTUBE_API_URL.format(api_key=api_key),
            json={
                "context": INNERTUBE_CONTEXT,
                "videoId": video_id,
            },
        )
        data = _raise_http_errors(response, video_id).json()
        return data


class _TranscriptParserAsync:
    _FORMATTING_TAGS = [
        "strong",  # important
        "em",  # emphasized
        "b",  # bold
        "i",  # italic
        "mark",  # marked
        "small",  # smaller
        "del",  # deleted
        "ins",  # inserted
        "sub",  # subscript
        "sup",  # superscript
    ]

    def __init__(self, preserve_formatting: bool = False):
        self._html_regex = self._get_html_regex(preserve_formatting)

    def _get_html_regex(self, preserve_formatting: bool) -> Pattern[str]:
        if preserve_formatting:
            formats_regex = "|".join(self._FORMATTING_TAGS)
            formats_regex = r"<\/?(?!\/?(" + formats_regex + r")\b).*?\b>"
            html_regex = re.compile(formats_regex, re.IGNORECASE)
        else:
            html_regex = re.compile(r"<[^>]*>", re.IGNORECASE)
        return html_regex

    def parse(self, raw_data: str) -> List[FetchedTranscriptSnippet]:
        return [
            FetchedTranscriptSnippet(
                text=re.sub(self._html_regex, "", unescape(xml_element.text)),
                start=float(xml_element.attrib["start"]),
                duration=float(xml_element.attrib.get("dur", "0.0")),
            )
            for xml_element in ElementTree.fromstring(raw_data)
            if xml_element.text is not None
        ]


@dataclass
class BulkFetchResults:
    video_id: str
    result: Union[FetchedTranscript, Dict[str, Any]]  # Either transcript or error dict

    def to_raw_data(self):
        return asdict(self)


class AsyncTranscriptHandler:
    def __init__(
        self,
        fetcher: TranscriptListFetcherAsync,
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
        async with self._semaphore:  # Add rate limiting
            transcript_list = await self._fetcher.fetch(video_id)
            transcript = transcript_list.find_transcript(languages)
            return await transcript.fetch(preserve_formatting=preserve_formatting)

    async def fetch_bulk(
        self,
        video_ids: List[str],
        languages: Iterable[str] = ("en",),
        preserve_formatting: bool = False,
    ) -> List[BulkFetchResults]:
        """Fetch transcripts for multiple videos concurrently with error handling"""

        async def _safe_fetch(video_id: str) -> Union[FetchedTranscript, Exception]:
            try:
                return await self.fetch_single(
                    video_id,
                    languages=languages,
                    preserve_formatting=preserve_formatting,
                )
            except Exception as e:
                return e

        # Create tasks with proper error handling
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
                        video_id=video_id, result=self._serialize_exception(result)
                    )
                )
            else:
                processed_results.append(
                    BulkFetchResults(video_id=video_id, result=result)
                )

        return processed_results
