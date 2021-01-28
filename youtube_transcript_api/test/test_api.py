from unittest import TestCase
from mock import patch

import os

import requests

import httpretty

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    TooManyRequests,
    NoTranscriptAvailable,
    NotTranslatable,
    TranslationLanguageNotAvailable,
    CookiePathInvalid,
    CookiesInvalid
)


def load_asset(filename):
    filepath = '{dirname}/assets/{filename}'.format(
        dirname=os.path.dirname(__file__), filename=filename)
    
    with open(filepath, mode="rb") as file:
        return file.read().decode('utf-8')


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

    def test_list_transcripts(self):
        transcript_list = YouTubeTranscriptApi.list_transcripts('GJLlxj_dtq8')

        language_codes = {transcript.language_code for transcript in transcript_list}

        self.assertEqual(language_codes, {'zh', 'de', 'en', 'hi', 'ja', 'ko', 'es', 'cs', 'en'})

    def test_list_transcripts__find_manually_created(self):
        transcript_list = YouTubeTranscriptApi.list_transcripts('GJLlxj_dtq8')
        transcript = transcript_list.find_manually_created_transcript(['cs'])

        self.assertFalse(transcript.is_generated)


    def test_list_transcripts__find_generated(self):
        transcript_list = YouTubeTranscriptApi.list_transcripts('GJLlxj_dtq8')

        with self.assertRaises(NoTranscriptFound):
            transcript_list.find_generated_transcript(['cs'])

        transcript = transcript_list.find_generated_transcript(['en'])

        self.assertTrue(transcript.is_generated)

    def test_translate_transcript(self):
        transcript = YouTubeTranscriptApi.list_transcripts('GJLlxj_dtq8').find_transcript(['en'])

        translated_transcript = transcript.translate('af')

        self.assertEqual(translated_transcript.language_code, 'af')
        self.assertIn('&tlang=af', translated_transcript._url)

    def test_translate_transcript__translation_language_not_available(self):
        transcript = YouTubeTranscriptApi.list_transcripts('GJLlxj_dtq8').find_transcript(['en'])

        with self.assertRaises(TranslationLanguageNotAvailable):
            transcript.translate('xyz')

    def test_translate_transcript__not_translatable(self):
        transcript = YouTubeTranscriptApi.list_transcripts('GJLlxj_dtq8').find_transcript(['en'])
        transcript.translation_languages = []

        with self.assertRaises(NotTranslatable):
            transcript.translate('af')

    def test_get_transcript__correct_language_is_used(self):
        YouTubeTranscriptApi.get_transcript('GJLlxj_dtq8', ['de', 'en'])
        query_string = httpretty.last_request().querystring

        self.assertIn('lang', query_string)
        self.assertEqual(len(query_string['lang']), 1)
        self.assertEqual(query_string['lang'][0], 'de')

    def test_get_transcript__fallback_language_is_used(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://www.youtube.com/watch',
            body=load_asset('youtube_ww1_nl_en.html.static')
        )

        YouTubeTranscriptApi.get_transcript('F1xioXWb8CY', ['de', 'en'])
        query_string = httpretty.last_request().querystring

        self.assertIn('lang', query_string)
        self.assertEqual(len(query_string['lang']), 1)
        self.assertEqual(query_string['lang'][0], 'en')

    def test_get_transcript__exception_if_video_unavailable(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://www.youtube.com/watch',
            body=load_asset('youtube_video_unavailable.html.static')
        )

        with self.assertRaises(VideoUnavailable):
            YouTubeTranscriptApi.get_transcript('abc')

    def test_get_transcript__exception_if_youtube_request_limit_reached(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://www.youtube.com/watch',
            body=load_asset('youtube_too_many_requests.html.static')
        )

        with self.assertRaises(TooManyRequests):
            YouTubeTranscriptApi.get_transcript('abc')

    def test_get_transcript__exception_if_transcripts_disabled(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://www.youtube.com/watch',
            body=load_asset('youtube_transcripts_disabled.html.static')
        )

        with self.assertRaises(TranscriptsDisabled):
            YouTubeTranscriptApi.get_transcript('dsMFmonKDD4')

    def test_get_transcript__exception_if_language_unavailable(self):
        with self.assertRaises(NoTranscriptFound):
            YouTubeTranscriptApi.get_transcript('GJLlxj_dtq8', languages=['cz'])

    def test_get_transcript__exception_if_no_transcript_available(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://www.youtube.com/watch',
            body=load_asset('youtube_no_transcript_available.html.static')
        )

        with self.assertRaises(NoTranscriptAvailable):
            YouTubeTranscriptApi.get_transcript('MwBPvcYFY2E')

    def test_get_transcript__with_proxy(self):
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
    
    def test_get_transcript__with_cookies(self):
        dirname, filename = os.path.split(os.path.abspath(__file__))
        cookies = dirname + '/example_cookies.txt'
        transcript = YouTubeTranscriptApi.get_transcript('GJLlxj_dtq8', cookies=cookies)

        self.assertEqual(
            transcript,
            [
                {'text': 'Hey, this is just a test', 'start': 0.0, 'duration': 1.54},
                {'text': 'this is not the original transcript', 'start': 1.54, 'duration': 4.16},
                {'text': 'just something shorter, I made up for testing', 'start': 5.7, 'duration': 3.239}
            ]
        )

    @patch('youtube_transcript_api.YouTubeTranscriptApi.get')
    def test_get_transcripts(self, mock_get_transcript):
        video_id_1 = 'video_id_1'
        video_id_2 = 'video_id_2'
        languages = ['de', 'en']

        YouTubeTranscriptApi.get_transcripts([video_id_1, video_id_2], languages=languages)

        mock_get_transcript.assert_any_call(video_id_1, languages)
        mock_get_transcript.assert_any_call(video_id_2, languages)
        self.assertEqual(mock_get_transcript.call_count, 2)

    @patch('youtube_transcript_api._transcripts.TranscriptListFetcher.fetch', side_effect=Exception('Error'))
    def test_get_transcripts__stop_on_error(self, mock_fetch):
        with self.assertRaises(Exception):
            YouTubeTranscriptApi.get_transcripts(['video_id_1', 'video_id_2'])

    @patch('youtube_transcript_api._transcripts.TranscriptListFetcher.fetch', side_effect=Exception('Error'))
    def test_get_transcripts__continue_on_error(self, mock_get_transcript):
        video_id_1 = 'video_id_1'
        video_id_2 = 'video_id_2'

        data, unretrievable_videos = YouTubeTranscriptApi.get_transcripts(['video_id_1', 'video_id_2'], continue_after_error=True)

        self.assertEqual(data, {})
        self.assertEqual(unretrievable_videos, [video_id_1, video_id_2])

    def test_load_cookies(self):
        dirname, filename = os.path.split(os.path.abspath(__file__))
        cookies = dirname + '/example_cookies.txt'
        session_cookies = YouTubeTranscriptApi._load_cookies(cookies, 'GJLlxj_dtq8')
        self.assertEqual({'TEST_FIELD': 'TEST_VALUE'},  requests.utils.dict_from_cookiejar(session_cookies))

    def test_load_cookies__bad_file_path(self):
        bad_cookies = 'nonexistent_cookies.txt'
        with self.assertRaises(CookiePathInvalid):
            YouTubeTranscriptApi._load_cookies(bad_cookies, 'GJLlxj_dtq8')

    def test_load_cookies__no_valid_cookies(self):
        dirname, filename = os.path.split(os.path.abspath(__file__))
        expired_cookies = dirname + '/expired_example_cookies.txt'
        with self.assertRaises(CookiesInvalid):
            YouTubeTranscriptApi._load_cookies(expired_cookies, 'GJLlxj_dtq8')
