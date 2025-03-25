from pathlib import Path
from typing import Iterable, Optional, List

from requests import HTTPError

from ._settings import WATCH_URL
from .proxies import ProxyConfig, GenericProxyConfig, WebshareProxyConfig


class YouTubeTranscriptApiException(Exception):
    pass


class CookieError(YouTubeTranscriptApiException):
    pass


class CookiePathInvalid(CookieError):
    def __init__(self, cookie_path: Path):
        super().__init__(f"Can't load the provided cookie file: {cookie_path}")


class CookieInvalid(CookieError):
    def __init__(self, cookie_path: Path):
        super().__init__(
            f"The cookies provided are not valid (may have expired): {cookie_path}"
        )


class CouldNotRetrieveTranscript(YouTubeTranscriptApiException):
    """
    Raised if a transcript could not be retrieved.
    """

    ERROR_MESSAGE = "\nCould not retrieve a transcript for the video {video_url}!"
    CAUSE_MESSAGE_INTRO = " This is most likely caused by:\n\n{cause}"
    CAUSE_MESSAGE = ""
    GITHUB_REFERRAL = (
        "\n\nIf you are sure that the described cause is not responsible for this error "
        "and that a transcript should be retrievable, please create an issue at "
        "https://github.com/jdepoix/youtube-transcript-api/issues. "
        "Please add which version of youtube_transcript_api you are using "
        "and provide the information needed to replicate the error. "
        "Also make sure that there are no open issues which already describe your problem!"
    )

    def __init__(self, video_id: str):
        self.video_id = video_id
        super().__init__()

    def _build_error_message(self) -> str:
        error_message = self.ERROR_MESSAGE.format(
            video_url=WATCH_URL.format(video_id=self.video_id)
        )

        cause = self.cause
        if cause:
            error_message += (
                self.CAUSE_MESSAGE_INTRO.format(cause=cause) + self.GITHUB_REFERRAL
            )

        return error_message

    @property
    def cause(self) -> str:
        return self.CAUSE_MESSAGE

    def __str__(self) -> str:
        return self._build_error_message()


class YouTubeDataUnparsable(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = (
        "The data required to fetch the transcript is not parsable. This should "
        "not happen, please open an issue (make sure to include the video ID)!"
    )


class YouTubeRequestFailed(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = "Request to YouTube failed: {reason}"

    def __init__(self, video_id: str, http_error: HTTPError):
        self.reason = str(http_error)
        super().__init__(video_id)

    @property
    def cause(self) -> str:
        return self.CAUSE_MESSAGE.format(
            reason=self.reason,
        )


class VideoUnplayable(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = "The video is unplayable for the following reason: {reason}"
    SUBREASON_MESSAGE = "\n\nAdditional Details:\n{sub_reasons}"

    def __init__(self, video_id: str, reason: Optional[str], sub_reasons: List[str]):
        self.reason = reason
        self.sub_reasons = sub_reasons
        super().__init__(video_id)

    @property
    def cause(self):
        reason = "No reason specified!" if self.reason is None else self.reason
        if self.sub_reasons:
            sub_reasons = "\n".join(
                f" - {sub_reason}" for sub_reason in self.sub_reasons
            )
            reason = f"{reason}{self.SUBREASON_MESSAGE.format(sub_reasons=sub_reasons)}"
        return self.CAUSE_MESSAGE.format(
            reason=reason,
        )


class VideoUnavailable(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = "The video is no longer available"


class InvalidVideoId(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = (
        "You provided an invalid video id. Make sure you are using the video id and NOT the url!\n\n"
        'Do NOT run: `YouTubeTranscriptApi.get_transcript("https://www.youtube.com/watch?v=1234")`\n'
        'Instead run: `YouTubeTranscriptApi.get_transcript("1234")`'
    )


class RequestBlocked(CouldNotRetrieveTranscript):
    BASE_CAUSE_MESSAGE = (
        "YouTube is blocking requests from your IP. This usually is due to one of the "
        "following reasons:\n"
        "- You have done too many requests and your IP has been blocked by YouTube\n"
        "- You are doing requests from an IP belonging to a cloud provider (like AWS, "
        "Google Cloud Platform, Azure, etc.). Unfortunately, most IPs from cloud "
        "providers are blocked by YouTube.\n\n"
    )
    CAUSE_MESSAGE = (
        f"{BASE_CAUSE_MESSAGE}"
        "There are two things you can do to work around this:\n"
        '1. Use proxies to hide your IP address, as explained in the "Working around '
        'IP bans" section of the README '
        "(https://github.com/jdepoix/youtube-transcript-api"
        "?tab=readme-ov-file"
        "#working-around-ip-bans-requestblocked-or-ipblocked-exception).\n"
        "2. (NOT RECOMMENDED) If you authenticate your requests using cookies, you "
        "will be able to continue doing requests for a while. However, YouTube will "
        "eventually permanently ban the account that you have used to authenticate "
        "with! So only do this if you don't mind your account being banned!"
    )
    WITH_GENERIC_PROXY_CAUSE_MESSAGE = (
        "YouTube is blocking your requests, despite you using proxies. Keep in mind "
        "a proxy is just a way to hide your real IP behind the IP of that proxy, but "
        "there is no guarantee that the IP of that proxy won't be blocked as well.\n\n"
        "The only truly reliable way to prevent IP blocks is rotating through a large "
        "pool of residential IPs, by using a provider like Webshare "
        "(https://www.webshare.io/?referral_code=w0xno53eb50g), which provides you "
        "with a pool of >30M residential IPs (make sure to purchase "
        '"Residential" proxies, NOT "Proxy Server" or "Static Residential"!).\n\n'
        "You will find more information on how to easily integrate Webshare here: "
        "https://github.com/jdepoix/youtube-transcript-api"
        "?tab=readme-ov-file#using-webshare"
    )
    WITH_WEBSHARE_PROXY_CAUSE_MESSAGE = (
        "YouTube is blocking your requests, despite you using Webshare proxies. "
        'Please make sure that you have purchased "Residential" proxies and '
        'NOT "Proxy Server" or "Static Residential", as those won\'t work as '
        'reliably! The free tier also uses "Proxy Server" and will NOT work!\n\n'
        'The only reliable option is using "Residential" proxies (not "Static '
        'Residential"), as this allows you to rotate through a pool of over 30M IPs, '
        "which means you will always find an IP that hasn't been blocked by YouTube "
        "yet!\n\n"
        "You can support the development of this open source project by making your "
        "Webshare purchases through this affiliate link: "
        "https://www.webshare.io/?referral_code=w0xno53eb50g \n\n"
        "Thank you for your support! <3"
    )

    def __init__(self, video_id: str):
        self._proxy_config = None
        super().__init__(video_id)

    def with_proxy_config(
        self, proxy_config: Optional[ProxyConfig]
    ) -> "RequestBlocked":
        self._proxy_config = proxy_config
        return self

    @property
    def cause(self) -> str:
        if isinstance(self._proxy_config, WebshareProxyConfig):
            return self.WITH_WEBSHARE_PROXY_CAUSE_MESSAGE
        if isinstance(self._proxy_config, GenericProxyConfig):
            return self.WITH_GENERIC_PROXY_CAUSE_MESSAGE
        return super().cause


class IpBlocked(RequestBlocked):
    CAUSE_MESSAGE = (
        f"{RequestBlocked.BASE_CAUSE_MESSAGE}"
        'Ways to work around this are explained in the "Working around IP '
        'bans" section of the README (https://github.com/jdepoix/youtube-transcript-api'
        "?tab=readme-ov-file"
        "#working-around-ip-bans-requestblocked-or-ipblocked-exception).\n"
    )


class TranscriptsDisabled(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = "Subtitles are disabled for this video"


class AgeRestricted(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = (
        "This video is age-restricted. Therefore, you will have to authenticate to be "
        "able to retrieve transcripts for it. You will have to provide a cookie to "
        'authenticate yourself, as explained in the "Cookie Authentication" section of '
        "the README (https://github.com/jdepoix/youtube-transcript-api"
        "?tab=readme-ov-file#cookie-authentication)"
    )


class NotTranslatable(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = "The requested language is not translatable"


class TranslationLanguageNotAvailable(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = "The requested translation language is not available"


class FailedToCreateConsentCookie(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = "Failed to automatically give consent to saving cookies"


class NoTranscriptFound(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = (
        "No transcripts were found for any of the requested language codes: {requested_language_codes}\n\n"
        "{transcript_data}"
    )

    def __init__(
        self,
        video_id: str,
        requested_language_codes: Iterable[str],
        transcript_data: "TranscriptList",  # noqa: F821
    ):
        self._requested_language_codes = requested_language_codes
        self._transcript_data = transcript_data
        super().__init__(video_id)

    @property
    def cause(self) -> str:
        return self.CAUSE_MESSAGE.format(
            requested_language_codes=self._requested_language_codes,
            transcript_data=str(self._transcript_data),
        )
