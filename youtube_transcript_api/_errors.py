from pathlib import Path
from typing import Iterable, Optional, List

from requests import HTTPError

from ._settings import WATCH_URL


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
        super().__init__(self._build_error_message())

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
