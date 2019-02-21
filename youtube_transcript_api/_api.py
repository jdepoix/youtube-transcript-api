import sys

if sys.version_info.major == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

from xml.etree import ElementTree

import re

import logging

import requests

from ._html_unescaping import unescape


logger = logging.getLogger(__name__)


class YouTubeTranscriptApi():
    class CouldNotRetrieveTranscript(Exception):
        """
        Raised if a transcript could not be retrieved.
        """

        ERROR_MESSAGE = (
            'Could not get the transcript for the video {video_url}! '
            'Most likely subtitles have been disabled by the uploader or the video is no longer '
            'available.'
        )

        def __init__(self, video_id):
            super(YouTubeTranscriptApi.CouldNotRetrieveTranscript, self).__init__(
                self.ERROR_MESSAGE.format(video_url=_TranscriptFetcher.WATCH_URL.format(video_id=video_id))
            )
            self.video_id = video_id

    @staticmethod
    def get_transcripts(video_ids, languages=None, continue_after_error=False):
        """
        Retrieves the transcripts for a list of videos.

        :param video_ids: a list of youtube video ids
        :type video_ids: [str]
        :param languages: A list of language codes in a descending priority. For example, if this is set to ['de', 'en']
        it will first try to fetch the german transcript (de) and then fetch the english transcipt (en) if it fails to
        do so. As I can't provide a complete list of all working language codes with full certainty, you may have to
        play around with the language codes a bit, to find the one which is working for you!
        :type languages: [str]
        :param continue_after_error: if this is set the execution won't be stopped, if an error occurs while retrieving
        one of the video transcripts
        :type continue_after_error: bool
        :return: a tuple containing a dictionary mapping video ids onto their corresponding transcripts, and a list of
        video ids, which could not be retrieved
        :rtype: ({str: [{'text': str, 'start': float, 'end': float}]}, [str]}
        """
        data = {}
        unretrievable_videos = []

        for video_id in video_ids:
            try:
                data[video_id] = YouTubeTranscriptApi.get_transcript(video_id, languages)
            except Exception as exception:
                if not continue_after_error:
                    raise exception

                unretrievable_videos.append(video_id)

        return data, unretrievable_videos

    @staticmethod
    def get_transcript(video_id, languages=None):
        """
        Retrieves the transcript for a single video.

        :param video_id: the youtube video id
        :type video_id: str
        :param languages: A list of language codes in a descending priority. For example, if this is set to ['de', 'en']
        it will first try to fetch the german transcript (de) and then fetch the english transcipt (en) if it fails to
        do so. As I can't provide a complete list of all working language codes with full certainty, you may have to
        play around with the language codes a bit, to find the one which is working for you!
        :type languages: [str]
        :return: a list of dictionaries containing the 'text', 'start' and 'duration' keys
        :rtype: [{'text': str, 'start': float, 'end': float}]
        """
        try:
            return _TranscriptParser(_TranscriptFetcher(video_id, languages).fetch()).parse()
        except Exception:
            logger.error(
                YouTubeTranscriptApi.CouldNotRetrieveTranscript.ERROR_MESSAGE.format(
                    video_url=_TranscriptFetcher.WATCH_URL.format(video_id=video_id)
                )
            )
            raise YouTubeTranscriptApi.CouldNotRetrieveTranscript(video_id)


class _TranscriptFetcher():
    WATCH_URL = 'https://www.youtube.com/watch?v={video_id}'
    API_BASE_URL = 'https://www.youtube.com/api/{api_url}'
    LANGUAGE_REGEX = re.compile(r'(&lang=.*&)|(&lang=.*)')

    def __init__(self, video_id, languages):
        self.video_id = video_id
        self.languages = languages

    def fetch(self):
        fetched_site = requests.get(self.WATCH_URL.format(video_id=self.video_id)).text
        timedtext_url_start = fetched_site.find('timedtext')

        for language in (self.languages if self.languages else [None,]):
            response = self._execute_api_request(fetched_site, timedtext_url_start, language)
            if response:
                return response

        return None

    def _execute_api_request(self, fetched_site, timedtext_url_start, language):
        url = self.API_BASE_URL.format(
            api_url=fetched_site[
                timedtext_url_start:timedtext_url_start + fetched_site[timedtext_url_start:].find('"')
            ].replace(
                '\\u0026', '&'
            ).replace(
                '\\', ''
            )
        )
        if language:
            url = re.sub(self.LANGUAGE_REGEX, '&lang={language}&'.format(language=language), url)
        return requests.get(url).text


class _TranscriptParser():
    HTML_TAG_REGEX = re.compile(r'<[^>]*>', re.IGNORECASE)

    def __init__(self, plain_data):
        self.plain_data = plain_data

    def parse(self):
        return [
            {
                'text': re.sub(self.HTML_TAG_REGEX, '', unescape(xml_element.text)),
                'start': float(xml_element.attrib['start']),
                'duration': float(xml_element.attrib['dur']),
            }
            for xml_element in ElementTree.fromstring(self.plain_data)
        ]
