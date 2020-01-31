from ._settings import WATCH_URL


class CouldNotRetrieveTranscript(Exception):
    """
    Raised if a transcript could not be retrieved.
    """
    ERROR_MESSAGE = '\nCould not retrieve a transcript for the video {video_url}!'
    CAUSE_MESSAGE_INTRO = ' This is most likely caused by:\n\n{cause}'
    CAUSE_MESSAGE = ''
    GITHUB_REFERRAL = (
        '\n\nIf you are sure that the described cause is not responsible for this error '
        'and that a transcript should be retrievable, please create an issue at '
        'https://github.com/jdepoix/youtube-transcript-api/issues. '
        'Please add which version of youtube_transcript_api you are using '
        'and provide the information needed to replicate the error. '
        'Also make sure that there are no open issues which already describe your problem!'
    )

    def __init__(self, video_id):
        self.video_id = video_id
        super(CouldNotRetrieveTranscript, self).__init__(self._build_error_message())

    def _build_error_message(self):
        cause = self.cause
        error_message = self.ERROR_MESSAGE.format(video_url=WATCH_URL.format(video_id=self.video_id))

        if cause:
            error_message += self.CAUSE_MESSAGE_INTRO.format(cause=cause) + self.GITHUB_REFERRAL

        return error_message

    @property
    def cause(self):
        return self.CAUSE_MESSAGE


class VideoUnavailable(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = 'The video is no longer available'


class TranscriptsDisabled(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = 'Subtitles are disabled for this video'


class NoTranscriptAvailable(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = 'No transcripts are available for this video'


class NotTranslatable(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = 'The requested language is not translatable'


class TranslationLanguageNotAvailable(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = 'The requested translation language is not available'


class CookiePathInvalid(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = 'The provided cookie file was unable to be loaded'


class CookiesInvalid(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = 'The cookies provided are not valid (may have expired)'


class NoTranscriptFound(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = (
        'No transcripts were found for any of the requested language codes: {requested_language_codes}\n\n'
        '{transcript_data}'
    )

    def __init__(self, video_id, requested_language_codes, transcript_data):
        self._requested_language_codes = requested_language_codes
        self._transcript_data = transcript_data
        super(NoTranscriptFound, self).__init__(video_id)

    @property
    def cause(self):
        return self.CAUSE_MESSAGE.format(
            requested_language_codes=self._requested_language_codes,
            transcript_data=str(self._transcript_data),
        )
