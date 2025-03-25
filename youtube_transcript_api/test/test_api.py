import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import requests

import httpretty

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    IpBlocked,
    NotTranslatable,
    TranslationLanguageNotAvailable,
    CookiePathInvalid,
    CookieInvalid,
    FailedToCreateConsentCookie,
    YouTubeRequestFailed,
    InvalidVideoId,
    FetchedTranscript,
    FetchedTranscriptSnippet,
    AgeRestricted,
    RequestBlocked,
    VideoUnplayable,
)
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig


def get_asset_path(filename: str) -> Path:
    return Path(
        "{dirname}/assets/{filename}".format(
            dirname=os.path.dirname(__file__), filename=filename
        )
    )


def load_asset(filename: str):
    with open(get_asset_path(filename), mode="rb") as file:
        return file.read()


class TestYouTubeTranscriptApi(TestCase):
    def setUp(self):
        self.ref_transcript = FetchedTranscript(
            snippets=[
                FetchedTranscriptSnippet(
                    text="Hey, this is just a test",
                    start=0.0,
                    duration=1.54,
                ),
                FetchedTranscriptSnippet(
                    text="this is not the original transcript",
                    start=1.54,
                    duration=4.16,
                ),
                FetchedTranscriptSnippet(
                    text="just something shorter, I made up for testing",
                    start=5.7,
                    duration=3.239,
                ),
            ],
            language="English",
            language_code="en",
            is_generated=False,
            video_id="GJLlxj_dtq8",
        )
        self.ref_transcript_raw = self.ref_transcript.to_raw_data()
        httpretty.enable()
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube.html.static"),
        )
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/api/timedtext",
            body=load_asset("transcript.xml.static"),
        )

    def tearDown(self):
        httpretty.reset()
        httpretty.disable()

    def test_fetch(self):
        transcript = YouTubeTranscriptApi().fetch("GJLlxj_dtq8")

        self.assertEqual(
            transcript,
            self.ref_transcript,
        )

    def test_fetch_formatted(self):
        transcript = YouTubeTranscriptApi().fetch(
            "GJLlxj_dtq8", preserve_formatting=True
        )

        self.ref_transcript[1].text = "this is <i>not</i> the original transcript"

        self.assertEqual(
            transcript,
            self.ref_transcript,
        )

    def test_fetch__with_altered_user_agent(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_altered_user_agent.html.static"),
        )

        transcript = YouTubeTranscriptApi().fetch("GJLlxj_dtq8")

        self.assertEqual(
            transcript,
            self.ref_transcript,
        )

    def test_list(self):
        transcript_list = YouTubeTranscriptApi().list("GJLlxj_dtq8")

        language_codes = {transcript.language_code for transcript in transcript_list}

        self.assertEqual(
            language_codes, {"zh", "de", "en", "hi", "ja", "ko", "es", "cs", "en"}
        )

    def test_list__find_manually_created(self):
        transcript_list = YouTubeTranscriptApi().list("GJLlxj_dtq8")
        transcript = transcript_list.find_manually_created_transcript(["cs"])

        self.assertFalse(transcript.is_generated)

    def test_list__find_generated(self):
        transcript_list = YouTubeTranscriptApi().list("GJLlxj_dtq8")

        with self.assertRaises(NoTranscriptFound):
            transcript_list.find_generated_transcript(["cs"])

        transcript = transcript_list.find_generated_transcript(["en"])

        self.assertTrue(transcript.is_generated)

    def test_list__url_as_video_id(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_video_unavailable.html.static"),
        )

        with self.assertRaises(InvalidVideoId):
            YouTubeTranscriptApi().list("https://www.youtube.com/watch?v=GJLlxj_dtq8")

    def test_list__no_translation_languages_provided(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_no_translation_languages.html.static"),
        )

        transcript_list = YouTubeTranscriptApi().list("GJLlxj_dtq8")
        for transcript in transcript_list:
            self.assertEqual(len(transcript.translation_languages), 0)

    def test_translate_transcript(self):
        transcript = YouTubeTranscriptApi().list("GJLlxj_dtq8").find_transcript(["en"])

        translated_transcript = transcript.translate("af")

        self.assertEqual(translated_transcript.language_code, "af")
        self.assertIn("&tlang=af", translated_transcript._url)

    def test_translate_transcript__translation_language_not_available(self):
        transcript = YouTubeTranscriptApi().list("GJLlxj_dtq8").find_transcript(["en"])

        with self.assertRaises(TranslationLanguageNotAvailable):
            transcript.translate("xyz")

    def test_translate_transcript__not_translatable(self):
        transcript = YouTubeTranscriptApi().list("GJLlxj_dtq8").find_transcript(["en"])
        transcript.translation_languages = []

        with self.assertRaises(NotTranslatable):
            transcript.translate("af")

    def test_fetch__correct_language_is_used(self):
        YouTubeTranscriptApi().fetch("GJLlxj_dtq8", ["de", "en"])
        query_string = httpretty.last_request().querystring

        self.assertIn("lang", query_string)
        self.assertEqual(len(query_string["lang"]), 1)
        self.assertEqual(query_string["lang"][0], "de")

    def test_fetch__fallback_language_is_used(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_ww1_nl_en.html.static"),
        )

        YouTubeTranscriptApi().fetch("F1xioXWb8CY", ["de", "en"])
        query_string = httpretty.last_request().querystring

        self.assertIn("lang", query_string)
        self.assertEqual(len(query_string["lang"]), 1)
        self.assertEqual(query_string["lang"][0], "en")

    def test_fetch__create_consent_cookie_if_needed(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_consent_page.html.static"),
        )

        YouTubeTranscriptApi().fetch("F1xioXWb8CY")
        self.assertEqual(len(httpretty.latest_requests()), 3)
        for request in httpretty.latest_requests()[1:]:
            self.assertEqual(
                request.headers["cookie"], "CONSENT=YES+cb.20210328-17-p0.de+FX+119"
            )

    def test_fetch__exception_if_create_consent_cookie_failed(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_consent_page.html.static"),
        )
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_consent_page.html.static"),
        )

        with self.assertRaises(FailedToCreateConsentCookie):
            YouTubeTranscriptApi().fetch("F1xioXWb8CY")

    def test_fetch__exception_if_consent_cookie_age_invalid(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_consent_page_invalid.html.static"),
        )

        with self.assertRaises(FailedToCreateConsentCookie):
            YouTubeTranscriptApi().fetch("F1xioXWb8CY")

    def test_fetch__exception_if_video_unavailable(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_video_unavailable.html.static"),
        )

        with self.assertRaises(VideoUnavailable):
            YouTubeTranscriptApi().fetch("abc")

    def test_fetch__exception_if_youtube_request_fails(self):
        httpretty.register_uri(
            httpretty.GET, "https://www.youtube.com/watch", status=500
        )

        with self.assertRaises(YouTubeRequestFailed) as cm:
            YouTubeTranscriptApi().fetch("abc")

        self.assertIn("Request to YouTube failed: ", str(cm.exception))

    def test_fetch__exception_if_age_restricted(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_age_restricted.html.static"),
        )

        with self.assertRaises(AgeRestricted):
            YouTubeTranscriptApi().fetch("Njp5uhTorCo")

    def test_fetch__exception_if_ip_blocked(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_too_many_requests.html.static"),
        )

        with self.assertRaises(IpBlocked):
            YouTubeTranscriptApi().fetch("abc")

    def test_fetch__exception_request_blocked(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_request_blocked.html.static"),
        )

        with self.assertRaises(RequestBlocked) as cm:
            YouTubeTranscriptApi().fetch("Njp5uhTorCo")

        self.assertIn("YouTube is blocking requests from your IP", str(cm.exception))

    def test_fetch__exception_unplayable(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_unplayable.html.static"),
        )

        with self.assertRaises(VideoUnplayable) as cm:
            YouTubeTranscriptApi().fetch("Njp5uhTorCo")
        exception = cm.exception
        self.assertEqual(exception.reason, "Custom Reason")
        self.assertEqual(exception.sub_reasons, ["Sub Reason 1", "Sub Reason 2"])
        self.assertIn("Custom Reason", str(exception))

    def test_fetch__exception_if_transcripts_disabled(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_transcripts_disabled.html.static"),
        )

        with self.assertRaises(TranscriptsDisabled):
            YouTubeTranscriptApi().fetch("dsMFmonKDD4")

        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_transcripts_disabled2.html.static"),
        )
        with self.assertRaises(TranscriptsDisabled):
            YouTubeTranscriptApi().fetch("Fjg5lYqvzUs")

    def test_fetch__exception_if_language_unavailable(self):
        with self.assertRaises(NoTranscriptFound) as cm:
            YouTubeTranscriptApi().fetch("GJLlxj_dtq8", languages=["cz"])

        self.assertIn("No transcripts were found for", str(cm.exception))

    @patch("youtube_transcript_api.proxies.GenericProxyConfig.to_requests_dict")
    def test_fetch__with_proxy(self, to_requests_dict):
        proxy_config = GenericProxyConfig(
            http_url="http://localhost:8080",
            https_url="http://localhost:8080",
        )
        transcript = YouTubeTranscriptApi(proxy_config=proxy_config).fetch(
            "GJLlxj_dtq8"
        )
        self.assertEqual(
            transcript,
            self.ref_transcript,
        )
        to_requests_dict.assert_any_call()

    @patch("youtube_transcript_api.proxies.GenericProxyConfig.to_requests_dict")
    def test_fetch__with_proxy_prevent_alive_connections(self, to_requests_dict):
        proxy_config = WebshareProxyConfig(
            proxy_username="username", proxy_password="password"
        )

        YouTubeTranscriptApi(proxy_config=proxy_config).fetch("GJLlxj_dtq8")

        request = httpretty.last_request()
        self.assertEqual(request.headers.get("Connection"), "close")

    @patch("youtube_transcript_api.proxies.GenericProxyConfig.to_requests_dict")
    def test_fetch__with_proxy_retry_when_blocked(self, to_requests_dict):
        for _ in range(3):
            httpretty.register_uri(
                httpretty.GET,
                "https://www.youtube.com/watch",
                body=load_asset("youtube_request_blocked.html.static"),
            )
        proxy_config = WebshareProxyConfig(
            proxy_username="username",
            proxy_password="password",
        )

        YouTubeTranscriptApi(proxy_config=proxy_config).fetch("Njp5uhTorCo")

        self.assertEqual(len(httpretty.latest_requests()), 3 + 2)

    @patch("youtube_transcript_api.proxies.GenericProxyConfig.to_requests_dict")
    def test_fetch__with_webshare_proxy_reraise_when_blocked(self, to_requests_dict):
        retries = 5
        for _ in range(retries):
            httpretty.register_uri(
                httpretty.GET,
                "https://www.youtube.com/watch",
                body=load_asset("youtube_request_blocked.html.static"),
            )
        proxy_config = WebshareProxyConfig(
            proxy_username="username",
            proxy_password="password",
            retries_when_blocked=retries,
        )

        with self.assertRaises(RequestBlocked) as cm:
            YouTubeTranscriptApi(proxy_config=proxy_config).fetch("Njp5uhTorCo")

        self.assertEqual(len(httpretty.latest_requests()), retries)
        self.assertEqual(cm.exception._proxy_config, proxy_config)
        self.assertIn("Webshare", str(cm.exception))

    @patch("youtube_transcript_api.proxies.GenericProxyConfig.to_requests_dict")
    def test_fetch__with_generic_proxy_reraise_when_blocked(self, to_requests_dict):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_request_blocked.html.static"),
        )
        proxy_config = GenericProxyConfig(
            http_url="http://localhost:8080",
            https_url="http://localhost:8080",
        )

        with self.assertRaises(RequestBlocked) as cm:
            YouTubeTranscriptApi(proxy_config=proxy_config).fetch("Njp5uhTorCo")

        self.assertEqual(len(httpretty.latest_requests()), 1)
        self.assertEqual(cm.exception._proxy_config, proxy_config)
        self.assertIn("YouTube is blocking your requests", str(cm.exception))

    def test_fetch__with_cookies(self):
        cookie_path = get_asset_path("example_cookies.txt")
        transcript = YouTubeTranscriptApi(cookie_path=cookie_path).fetch("GJLlxj_dtq8")

        self.assertEqual(
            transcript,
            self.ref_transcript,
        )

    def test_load_cookies(self):
        cookie_path = get_asset_path("example_cookies.txt")

        ytt_api = YouTubeTranscriptApi(cookie_path=cookie_path)

        session_cookies = ytt_api._fetcher._http_client.cookies
        self.assertEqual(
            {"TEST_FIELD": "TEST_VALUE"},
            requests.utils.dict_from_cookiejar(session_cookies),
        )

    def test_load_cookies__bad_file_path(self):
        cookie_path = get_asset_path("nonexistent_cookies.txt")
        with self.assertRaises(CookiePathInvalid):
            YouTubeTranscriptApi(cookie_path=cookie_path)

    def test_load_cookies__no_valid_cookies(self):
        cookie_path = get_asset_path("expired_example_cookies.txt")
        with self.assertRaises(CookieInvalid):
            YouTubeTranscriptApi(cookie_path=cookie_path)

    ### DEPRECATED METHODS ###

    def test_get_transcript__deprecated(self):
        transcript = YouTubeTranscriptApi.get_transcript("GJLlxj_dtq8")

        self.assertEqual(
            transcript,
            [
                {"text": "Hey, this is just a test", "start": 0.0, "duration": 1.54},
                {
                    "text": "this is not the original transcript",
                    "start": 1.54,
                    "duration": 4.16,
                },
                {
                    "text": "just something shorter, I made up for testing",
                    "start": 5.7,
                    "duration": 3.239,
                },
            ],
        )

    def test_get_transcript_formatted__deprecated(self):
        transcript = YouTubeTranscriptApi.get_transcript(
            "GJLlxj_dtq8", preserve_formatting=True
        )

        self.assertEqual(
            transcript,
            [
                {"text": "Hey, this is just a test", "start": 0.0, "duration": 1.54},
                {
                    "text": "this is <i>not</i> the original transcript",
                    "start": 1.54,
                    "duration": 4.16,
                },
                {
                    "text": "just something shorter, I made up for testing",
                    "start": 5.7,
                    "duration": 3.239,
                },
            ],
        )

    def test_list_transcripts__deprecated(self):
        transcript_list = YouTubeTranscriptApi.list_transcripts("GJLlxj_dtq8")

        language_codes = {transcript.language_code for transcript in transcript_list}

        self.assertEqual(
            language_codes, {"zh", "de", "en", "hi", "ja", "ko", "es", "cs", "en"}
        )

    def test_list_transcripts__find_manually_created__deprecated(self):
        transcript_list = YouTubeTranscriptApi.list_transcripts("GJLlxj_dtq8")
        transcript = transcript_list.find_manually_created_transcript(["cs"])

        self.assertFalse(transcript.is_generated)

    def test_list_transcripts__find_generated__deprecated(self):
        transcript_list = YouTubeTranscriptApi.list_transcripts("GJLlxj_dtq8")

        with self.assertRaises(NoTranscriptFound):
            transcript_list.find_generated_transcript(["cs"])

        transcript = transcript_list.find_generated_transcript(["en"])

        self.assertTrue(transcript.is_generated)

    def test_list_transcripts__url_as_video_id__deprecated(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_video_unavailable.html.static"),
        )

        with self.assertRaises(InvalidVideoId):
            YouTubeTranscriptApi.list_transcripts(
                "https://www.youtube.com/watch?v=GJLlxj_dtq8"
            )

    def test_list_transcripts__no_translation_languages_provided__deprecated(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_no_translation_languages.html.static"),
        )

        transcript_list = YouTubeTranscriptApi.list_transcripts("GJLlxj_dtq8")
        for transcript in transcript_list:
            self.assertEqual(len(transcript.translation_languages), 0)

    def test_translate_transcript__deprecated(self):
        transcript = YouTubeTranscriptApi.list_transcripts(
            "GJLlxj_dtq8"
        ).find_transcript(["en"])

        translated_transcript = transcript.translate("af")

        self.assertEqual(translated_transcript.language_code, "af")
        self.assertIn("&tlang=af", translated_transcript._url)

    def test_translate_transcript__translation_language_not_available__deprecated(self):
        transcript = YouTubeTranscriptApi.list_transcripts(
            "GJLlxj_dtq8"
        ).find_transcript(["en"])

        with self.assertRaises(TranslationLanguageNotAvailable):
            transcript.translate("xyz")

    def test_translate_transcript__not_translatable__deprecated(self):
        transcript = YouTubeTranscriptApi.list_transcripts(
            "GJLlxj_dtq8"
        ).find_transcript(["en"])
        transcript.translation_languages = []

        with self.assertRaises(NotTranslatable):
            transcript.translate("af")

    def test_get_transcript__correct_language_is_used__deprecated(self):
        YouTubeTranscriptApi.get_transcript("GJLlxj_dtq8", ["de", "en"])
        query_string = httpretty.last_request().querystring

        self.assertIn("lang", query_string)
        self.assertEqual(len(query_string["lang"]), 1)
        self.assertEqual(query_string["lang"][0], "de")

    def test_get_transcript__fallback_language_is_used__deprecated(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_ww1_nl_en.html.static"),
        )

        YouTubeTranscriptApi.get_transcript("F1xioXWb8CY", ["de", "en"])
        query_string = httpretty.last_request().querystring

        self.assertIn("lang", query_string)
        self.assertEqual(len(query_string["lang"]), 1)
        self.assertEqual(query_string["lang"][0], "en")

    def test_get_transcript__create_consent_cookie_if_needed__deprecated(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_consent_page.html.static"),
        )

        YouTubeTranscriptApi.get_transcript("F1xioXWb8CY")
        self.assertEqual(len(httpretty.latest_requests()), 3)
        for request in httpretty.latest_requests()[1:]:
            self.assertEqual(
                request.headers["cookie"], "CONSENT=YES+cb.20210328-17-p0.de+FX+119"
            )

    def test_get_transcript__exception_if_create_consent_cookie_failed__deprecated(
        self,
    ):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_consent_page.html.static"),
        )
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_consent_page.html.static"),
        )

        with self.assertRaises(FailedToCreateConsentCookie):
            YouTubeTranscriptApi.get_transcript("F1xioXWb8CY")

    def test_get_transcript__exception_if_consent_cookie_age_invalid__deprecated(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_consent_page_invalid.html.static"),
        )

        with self.assertRaises(FailedToCreateConsentCookie):
            YouTubeTranscriptApi.get_transcript("F1xioXWb8CY")

    def test_get_transcript__exception_if_video_unavailable__deprecated(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_video_unavailable.html.static"),
        )

        with self.assertRaises(VideoUnavailable):
            YouTubeTranscriptApi.get_transcript("abc")

    def test_get_transcript__exception_if_youtube_request_fails__deprecated(self):
        httpretty.register_uri(
            httpretty.GET, "https://www.youtube.com/watch", status=500
        )

        with self.assertRaises(YouTubeRequestFailed):
            YouTubeTranscriptApi.get_transcript("abc")

    def test_get_transcript__exception_if_youtube_request_limit_reached__deprecated(
        self,
    ):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_too_many_requests.html.static"),
        )

        with self.assertRaises(IpBlocked):
            YouTubeTranscriptApi.get_transcript("abc")

    def test_get_transcript__exception_if_transcripts_disabled__deprecated(self):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_transcripts_disabled.html.static"),
        )

        with self.assertRaises(TranscriptsDisabled):
            YouTubeTranscriptApi.get_transcript("dsMFmonKDD4")

        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_transcripts_disabled2.html.static"),
        )
        with self.assertRaises(TranscriptsDisabled):
            YouTubeTranscriptApi.get_transcript("Fjg5lYqvzUs")

    def test_get_transcript__exception_if_language_unavailable__deprecated(self):
        with self.assertRaises(NoTranscriptFound):
            YouTubeTranscriptApi.get_transcript("GJLlxj_dtq8", languages=["cz"])

    @patch("youtube_transcript_api.proxies.GenericProxyConfig.to_requests_dict")
    def test_get_transcript__with_proxy__deprecated(self, to_requests_dict):
        proxies = {
            "http": "http://localhost:8080",
            "https": "http://localhost:8080",
        }
        transcript = YouTubeTranscriptApi.get_transcript("GJLlxj_dtq8", proxies=proxies)
        self.assertEqual(
            transcript,
            [
                {"text": "Hey, this is just a test", "start": 0.0, "duration": 1.54},
                {
                    "text": "this is not the original transcript",
                    "start": 1.54,
                    "duration": 4.16,
                },
                {
                    "text": "just something shorter, I made up for testing",
                    "start": 5.7,
                    "duration": 3.239,
                },
            ],
        )
        to_requests_dict.assert_any_call()

    @patch("youtube_transcript_api.proxies.GenericProxyConfig.to_requests_dict")
    def test_get_transcript__with_proxy_config__deprecated(self, to_requests_dict):
        proxy_config = GenericProxyConfig(
            http_url="http://localhost:8080",
            https_url="http://localhost:8080",
        )
        transcript = YouTubeTranscriptApi.get_transcript(
            "GJLlxj_dtq8", proxies=proxy_config
        )
        self.assertEqual(
            transcript,
            [
                {"text": "Hey, this is just a test", "start": 0.0, "duration": 1.54},
                {
                    "text": "this is not the original transcript",
                    "start": 1.54,
                    "duration": 4.16,
                },
                {
                    "text": "just something shorter, I made up for testing",
                    "start": 5.7,
                    "duration": 3.239,
                },
            ],
        )
        to_requests_dict.assert_any_call()

    def test_get_transcript__with_cookies__deprecated(self):
        cookies_path = get_asset_path("example_cookies.txt")
        transcript = YouTubeTranscriptApi.get_transcript(
            "GJLlxj_dtq8", cookies=str(cookies_path)
        )

        self.assertEqual(
            transcript,
            [
                {"text": "Hey, this is just a test", "start": 0.0, "duration": 1.54},
                {
                    "text": "this is not the original transcript",
                    "start": 1.54,
                    "duration": 4.16,
                },
                {
                    "text": "just something shorter, I made up for testing",
                    "start": 5.7,
                    "duration": 3.239,
                },
            ],
        )

    def test_get_transcript__assertionerror_if_input_not_string__deprecated(self):
        with self.assertRaises(AssertionError):
            YouTubeTranscriptApi.get_transcript(["video_id_1", "video_id_2"])

    def test_get_transcripts__assertionerror_if_input_not_list__deprecated(self):
        with self.assertRaises(AssertionError):
            YouTubeTranscriptApi.get_transcripts("video_id_1")

    @patch("youtube_transcript_api.YouTubeTranscriptApi.get_transcript")
    def test_get_transcripts__deprecated(self, mock_get_transcript):
        video_id_1 = "video_id_1"
        video_id_2 = "video_id_2"
        languages = ["de", "en"]

        YouTubeTranscriptApi.get_transcripts(
            [video_id_1, video_id_2], languages=languages
        )

        mock_get_transcript.assert_any_call(video_id_1, languages, None, None, False)
        mock_get_transcript.assert_any_call(video_id_2, languages, None, None, False)
        self.assertEqual(mock_get_transcript.call_count, 2)

    @patch(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        side_effect=Exception("Error"),
    )
    def test_get_transcripts__stop_on_error__deprecated(self, mock_get_transcript):
        with self.assertRaises(Exception):
            YouTubeTranscriptApi.get_transcripts(["video_id_1", "video_id_2"])

    @patch(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        side_effect=Exception("Error"),
    )
    def test_get_transcripts__continue_on_error__deprecated(self, mock_get_transcript):
        video_id_1 = "video_id_1"
        video_id_2 = "video_id_2"

        YouTubeTranscriptApi.get_transcripts(
            ["video_id_1", "video_id_2"], continue_after_error=True
        )

        mock_get_transcript.assert_any_call(video_id_1, ("en",), None, None, False)
        mock_get_transcript.assert_any_call(video_id_2, ("en",), None, None, False)

    @patch("youtube_transcript_api.YouTubeTranscriptApi.get_transcript")
    def test_get_transcripts__with_cookies__deprecated(self, mock_get_transcript):
        cookie_path = get_asset_path("example_cookies.txt")
        YouTubeTranscriptApi.get_transcripts(["GJLlxj_dtq8"], cookies=str(cookie_path))
        mock_get_transcript.assert_any_call(
            "GJLlxj_dtq8", ("en",), None, str(cookie_path), False
        )

    @patch("youtube_transcript_api.YouTubeTranscriptApi.get_transcript")
    def test_get_transcripts__with_proxies__deprecated(self, mock_get_transcript):
        proxies = {
            "http": "http://localhost:8080",
            "https": "http://localhost:8080",
        }
        YouTubeTranscriptApi.get_transcripts(["GJLlxj_dtq8"], proxies=proxies)
        mock_get_transcript.assert_any_call(
            "GJLlxj_dtq8", ("en",), proxies, None, False
        )
