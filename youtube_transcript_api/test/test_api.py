from unittest import TestCase
from mock import MagicMock

import os

import httpretty

from youtube_transcript_api._api import YouTubeTranscriptApi


def load_asset(filename):
    with open('{dirname}/assets/{filename}'.format(dirname=os.path.dirname(__file__), filename=filename)) as file:
        return file.read()


class TestYouTubeTranscriptApi(TestCase):
    def setUp(self):
        httpretty.enable()
        httpretty.register_uri(
            httpretty.GET,
            'https://www.youtube.com/watch',
            body=load_asset('youtube.html.static')
        )
        httpretty.register_uri(
            httpretty.GET,
            'https://www.youtube.com/api/timedtext',
            body=load_asset('transcript.xml.static')
        )

    def tearDown(self):
        httpretty.disable()

    def test_get_transcript(self):
        transcript = YouTubeTranscriptApi.get_transcript('GJLlxj_dtq8')

        self.assertEqual(
            transcript,
            [
                {'text': 'Hey, this is just a test', 'start': 0.0, 'duration': 1.54},
                {'text': 'this is not the original transcript', 'start': 1.54, 'duration': 4.16},
                {'text': 'just something shorter, I made up for testing', 'start': 5.7, 'duration': 3.239}
            ]
        )

    def test_get_transcript__correct_language_is_used(self):
        YouTubeTranscriptApi.get_transcript('GJLlxj_dtq8', ['de', 'en'])
        query_string = httpretty.last_request().querystring

        self.assertIn('lang', query_string)
        self.assertEqual(len(query_string['lang']), 1)
        self.assertEqual(query_string['lang'][0], 'de')

    def test_get_transcript__fallback_language_is_used(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://www.youtube.com/api/timedtext',
            body=''
        )

        YouTubeTranscriptApi.get_transcript('GJLlxj_dtq8', ['de', 'en'])
        query_string = httpretty.last_request().querystring

        self.assertIn('lang', query_string)
        self.assertEqual(len(query_string['lang']), 1)
        self.assertEqual(query_string['lang'][0], 'en')

    def test_get_transcript__exception_is_raised_when_not_available(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://www.youtube.com/api/timedtext',
            body=''
        )

        with self.assertRaises(YouTubeTranscriptApi.CouldNotRetrieveTranscript):
            YouTubeTranscriptApi.get_transcript('GJLlxj_dtq8')

    def test_get_transcripts(self):
        video_id_1 = 'video_id_1'
        video_id_2 = 'video_id_2'
        languages = ['de', 'en']
        YouTubeTranscriptApi.get_transcript = MagicMock()

        YouTubeTranscriptApi.get_transcripts([video_id_1, video_id_2], languages=languages)

        YouTubeTranscriptApi.get_transcript.assert_any_call(video_id_1, languages, None)
        YouTubeTranscriptApi.get_transcript.assert_any_call(video_id_2, languages, None)
        self.assertEqual(YouTubeTranscriptApi.get_transcript.call_count, 2)

    def test_get_transcripts__stop_on_error(self):
        YouTubeTranscriptApi.get_transcript = MagicMock(side_effect=Exception('Error'))

        with self.assertRaises(Exception):
            YouTubeTranscriptApi.get_transcripts(['video_id_1', 'video_id_2'])

    def test_get_transcripts__continue_on_error(self):
        video_id_1 = 'video_id_1'
        video_id_2 = 'video_id_2'
        YouTubeTranscriptApi.get_transcript = MagicMock(side_effect=Exception('Error'))

        YouTubeTranscriptApi.get_transcripts(['video_id_1', 'video_id_2'], continue_after_error=True)

        YouTubeTranscriptApi.get_transcript.assert_any_call(video_id_1, None, None)
        YouTubeTranscriptApi.get_transcript.assert_any_call(video_id_2, None, None)

    def test_get_transcript__with_proxies(self):
        proxies = {'http': '', 'https:': ''}
        transcript = YouTubeTranscriptApi.get_transcript(
            'GJLlxj_dtq8', proxies=proxies
        )

        self.assertEqual(
            transcript,
            [
                {'text': 'Hey, this is just a test', 'start': 0.0, 'duration': 1.54},
                {'text': 'this is not the original transcript', 'start': 1.54, 'duration': 4.16},
                {'text': 'just something shorter, I made up for testing', 'start': 5.7, 'duration': 3.239}
            ]
        )
        YouTubeTranscriptApi.get_transcript = MagicMock()
        YouTubeTranscriptApi.get_transcripts(['GJLlxj_dtq8'], proxies=proxies)
        YouTubeTranscriptApi.get_transcript.assert_any_call('GJLlxj_dtq8', None, proxies)
