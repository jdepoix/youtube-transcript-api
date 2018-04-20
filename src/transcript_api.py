from xml.etree import ElementTree

import re

import logging

import requests


logger = logging.getLogger(__name__)


class YouTubeTranscriptApi():
    @staticmethod
    def get(*video_ids):
        data = {}

        for video_id in video_ids:
            try:
                data[video_id] = _TranscriptParser(_TranscriptFetcher(video_id).fetch()).parse()
            except Exception:
                logger.error(
                    'Could not get the transcript for the video {video_url}! '
                    'Most likely subtitles have been disabled by the uploader or the video is no longer '
                    'available.'.format(
                        video_url=_TranscriptFetcher.WATCH_URL.format(video_id=video_id)
                    )
                )

        return data


class _TranscriptFetcher():
    WATCH_URL = 'https://www.youtube.com/watch?v={video_id}'
    API_BASE_URL = 'https://www.youtube.com/api/{api_url}'

    def __init__(self, video_id):
        self.video_id = video_id

    def fetch(self):
        fetched_site = requests.get(self.WATCH_URL.format(video_id=self.video_id)).text

        timedtext_url_start = fetched_site.find('timedtext')

        return requests.get(
            self.API_BASE_URL.format(
                api_url=fetched_site[
                    timedtext_url_start:timedtext_url_start + fetched_site[timedtext_url_start:].find('"')
                ].replace(
                    '\\u0026', '&'
                ).replace(
                    '\\', ''
                )
            )
        ).text


class _TranscriptParser():
    HTML_TAG_REGEX = re.compile(r'<[^>]*>', re.IGNORECASE)

    def __init__(self, plain_data):
        self.plain_data = plain_data

    def parse(self):
        return [
            {
                'text': re.sub(self.HTML_TAG_REGEX, '', xml_element.text),
                'start': float(xml_element.attrib['start']),
                'duration': float(xml_element.attrib['dur']),
            }
            for xml_element in ElementTree.fromstring(self.plain_data)
        ]
