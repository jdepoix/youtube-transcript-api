import sys

# This can only be tested by using different python versions, therefore it is not covered by coverage.py
if sys.version_info.major == 2: # pragma: no cover
    reload(sys)
    sys.setdefaultencoding('utf-8')

import json

from xml.etree import ElementTree

import re

from ._html_unescaping import unescape
from ._errors import VideoUnavailable, NoTranscriptFound, TranscriptsDisabled
from ._settings import WATCH_URL


class TranscriptDataFetcher():
    def __init__(self, http_client):
        self._http_client = http_client

    def fetch(self, video_id):
        return TranscriptData.build(
            self._http_client,
            video_id,
            self._extract_captions_json(self._fetch_html(video_id), video_id)
        )

    def _extract_captions_json(self, html, video_id):
        splitted_html = html.split('"captions":')

        if len(splitted_html) <= 1:
            if '"playabilityStatus":' not in html:
                raise VideoUnavailable(video_id)

            raise TranscriptsDisabled(video_id)

        return json.loads(splitted_html[1].split(',"videoDetails')[0].replace('\n', ''))[
            'playerCaptionsTracklistRenderer'
        ]

    def _fetch_html(self, video_id):
        return self._http_client.get(WATCH_URL.format(video_id=video_id)).text.replace(
            '\\u0026', '&'
        ).replace(
            '\\', ''
        )


class TranscriptData():
    # TODO implement iterator

    def __init__(
        self, http_client, video_id, manually_created_transcripts, generated_transcripts, translation_languages
    ):
        self._http_client = http_client
        self.video_id = video_id
        self._manually_created_transcripts = manually_created_transcripts
        self._generated_transcripts = generated_transcripts
        self._translation_languages = translation_languages

    @staticmethod
    def build(http_client, video_id, captions_json):
        manually_created_transcripts = []
        generated_transcripts = []

        for caption in captions_json['captionTracks']:
            (generated_transcripts if caption.get('kind', '') == 'asr' else generated_transcripts).append(
                {
                    'url': caption['baseUrl'],
                    'language': caption['name']['simpleText'],
                    'language_code': caption['languageCode'],
                    'is_generated': caption.get('kind', '') == 'asr',
                    'is_translatable': caption['isTranslatable'],
                }
            )

        return TranscriptData(
            http_client,
            video_id,
            manually_created_transcripts,
            generated_transcripts,
            [
                {
                    'language': translation_language['languageName']['simpleText'],
                    'language_code': translation_language['languageCode'],
                } for translation_language in captions_json['translationLanguages']
            ],
        )

    def find_transcript(self, language_codes):
        try:
            return self.find_manually_created_transcript(language_codes)
        except NoTranscriptFound:
            pass

        return self.find_generated_transcript(language_codes)

    def find_generated_transcript(self, language_codes):
        return self._find_transcript(language_codes, generated=True)

    def find_manually_created_transcript(self, language_codes):
        return self._find_transcript(language_codes, generated=False)

    def _find_transcript(self, language_codes, generated):
        transcripts = self._generated_transcripts if generated else self._manually_created_transcripts

        for language_code in language_codes:
            for transcript in transcripts:
                if transcript['language_code'] == language_code:
                    return Transcript(
                        self._http_client,
                        transcript['url'],
                        transcript['language'],
                        transcript['language_code'],
                        transcript['is_generated'],
                        self._translation_languages if transcript['is_translatable'] else []
                    )

        raise NoTranscriptFound(
            self.video_id,
            language_codes,
            self
        )

    def __str__(self):
        return (
            'For this video ({video_id}) transcripts are available in the following languages:\n\n'
            '(MANUALLY CREATED)\n'
            '{available_manually_created_transcript_languages}\n\n'
            '(GENERATED)\n'
            '{available_generated_transcripts}'
        ).format(
            video_id=self.video_id,
            available_manually_created_transcript_languages=self._get_language_description(
                self._manually_created_transcripts
            ),
            available_generated_transcripts=self._get_language_description(
                self._generated_transcripts
            ),
        )

    def _get_language_description(self, transcripts):
        return '\n'.join(
            ' - {language_code} ("{language}")'.format(
                language=transcript['language'],
                language_code=transcript['language_code'],
            ) for transcript in transcripts
        ) if transcripts else 'None'


class Transcript():
    def __init__(self, http_client, url, language, language_code, is_generated, translation_languages):
        self._http_client = http_client
        self.url = url
        self.language = language
        self.language_code = language_code
        self.is_generated = is_generated
        self.translation_languages = translation_languages

    def fetch(self):
        return _TranscriptParser().parse(
            self._http_client.get(self.url).text
        )

# TODO integrate translations in future release
#     @property
#     def is_translatable(self):
#         return len(self.translation_languages) > 0
#
#
# class TranslatableTranscript(Transcript):
#     def __init__(self, http_client, url, translation_languages):
#         super(TranslatableTranscript, self).__init__(http_client, url)
#         self._translation_languages = translation_languages
#         self._translation_language_codes = {language['language_code'] for language in translation_languages}
#
#
#     def translate(self, language_code):
#         if language_code not in self._translation_language_codes:
#             raise TranslatableTranscript.TranslationLanguageNotAvailable()
#
#         return Transcript(
#             self._http_client,
#             '{url}&tlang={language_code}'.format(url=self._url, language_code=language_code)
#         )


class _TranscriptParser():
    HTML_TAG_REGEX = re.compile(r'<[^>]*>', re.IGNORECASE)

    def parse(self, plain_data):
        return [
            {
                'text': re.sub(self.HTML_TAG_REGEX, '', unescape(xml_element.text)),
                'start': float(xml_element.attrib['start']),
                'duration': float(xml_element.attrib['dur']),
            }
            for xml_element in ElementTree.fromstring(plain_data)
            if xml_element.text is not None
        ]
