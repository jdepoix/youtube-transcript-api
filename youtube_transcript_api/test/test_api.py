import pytest
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
    PoTokenRequired,
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
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube.innertube.json.static"),
        )
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
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_altered_user_agent.innertube.json.static"),
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
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_video_unavailable.innertube.json.static"),
        )

        with self.assertRaises(InvalidVideoId):
            YouTubeTranscriptApi().list(
                "https://www.youtube.com/youtubei/v1/player?v=GJLlxj_dtq8"
            )

    def test_translate_transcript(self):
        transcript = YouTubeTranscriptApi().list("GJLlxj_dtq8").find_transcript(["en"])

        translated_transcript = transcript.translate("ar")

        self.assertEqual(translated_transcript.language_code, "ar")
        self.assertIn("&tlang=ar", translated_transcript._url)

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
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_ww1_nl_en.innertube.json.static"),
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
        self.assertEqual(len(httpretty.latest_requests()), 4)
        for request in httpretty.latest_requests()[1:]:
            self.assertEqual(
                request.headers["cookie"], "CONSENT=YES+cb.20210328-17-p0.de+FX+119"
            )

    def test_fetch__exception_if_create_consent_cookie_failed(self):
        for _ in range(2):
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
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_video_unavailable.innertube.json.static"),
        )

        with self.assertRaises(VideoUnavailable):
            YouTubeTranscriptApi().fetch("abc")

    def test_fetch__exception_if_youtube_request_fails(self):
        httpretty.register_uri(
            httpretty.POST, "https://www.youtube.com/youtubei/v1/player", status=500
        )

        with self.assertRaises(YouTubeRequestFailed) as cm:
            YouTubeTranscriptApi().fetch("abc")

        self.assertIn("Request to YouTube failed: ", str(cm.exception))

    def test_fetch__exception_if_youtube_request_limit_reached(
        self,
    ):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/watch",
            body=load_asset("youtube_too_many_requests.html.static"),
        )

        with self.assertRaises(IpBlocked):
            YouTubeTranscriptApi().fetch("abc")

    def test_fetch__exception_if_timedtext_request_limit_reached(
        self,
    ):
        httpretty.register_uri(
            httpretty.GET,
            "https://www.youtube.com/api/timedtext",
            status=429,
        )

        with self.assertRaises(IpBlocked):
            YouTubeTranscriptApi().fetch("abc")

    def test_fetch__exception_if_age_restricted(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_age_restricted.innertube.json.static"),
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

    def test_fetch__exception_if_po_token_required(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_po_token_required.innertube.json.static"),
        )

        with self.assertRaises(PoTokenRequired):
            YouTubeTranscriptApi().fetch("GJLlxj_dtq8")

    def test_fetch__exception_request_blocked(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_request_blocked.innertube.json.static"),
        )

        with self.assertRaises(RequestBlocked) as cm:
            YouTubeTranscriptApi().fetch("Njp5uhTorCo")

        self.assertIn("YouTube is blocking requests from your IP", str(cm.exception))

    def test_fetch__exception_unplayable(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_unplayable.innertube.json.static"),
        )

        with self.assertRaises(VideoUnplayable) as cm:
            YouTubeTranscriptApi().fetch("Njp5uhTorCo")
        exception = cm.exception
        self.assertEqual(exception.reason, "Custom Reason")
        self.assertEqual(exception.sub_reasons, ["Sub Reason 1", "Sub Reason 2"])
        self.assertIn("Custom Reason", str(exception))

    def test_fetch__exception_if_transcripts_disabled(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_transcripts_disabled.innertube.json.static"),
        )

        with self.assertRaises(TranscriptsDisabled):
            YouTubeTranscriptApi().fetch("dsMFmonKDD4")

        httpretty.register_uri(
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_transcripts_disabled2.innertube.json.static"),
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
                httpretty.POST,
                "https://www.youtube.com/youtubei/v1/player",
                body=load_asset("youtube_request_blocked.innertube.json.static"),
            )
        proxy_config = WebshareProxyConfig(
            proxy_username="username",
            proxy_password="password",
        )

        YouTubeTranscriptApi(proxy_config=proxy_config).fetch("Njp5uhTorCo")

        self.assertEqual(len(httpretty.latest_requests()), 2 * 3 + 3)

    @patch("youtube_transcript_api.proxies.GenericProxyConfig.to_requests_dict")
    def test_fetch__with_webshare_proxy_reraise_when_blocked(self, to_requests_dict):
        retries = 5
        for _ in range(retries):
            httpretty.register_uri(
                httpretty.POST,
                "https://www.youtube.com/youtubei/v1/player",
                body=load_asset("youtube_request_blocked.innertube.json.static"),
            )
        proxy_config = WebshareProxyConfig(
            proxy_username="username",
            proxy_password="password",
            retries_when_blocked=retries,
        )

        with self.assertRaises(RequestBlocked) as cm:
            YouTubeTranscriptApi(proxy_config=proxy_config).fetch("Njp5uhTorCo")

        self.assertEqual(len(httpretty.latest_requests()), retries * 2)
        self.assertEqual(cm.exception._proxy_config, proxy_config)
        self.assertIn("Webshare", str(cm.exception))

    @patch("youtube_transcript_api.proxies.GenericProxyConfig.to_requests_dict")
    def test_fetch__with_generic_proxy_reraise_when_blocked(self, to_requests_dict):
        httpretty.register_uri(
            httpretty.POST,
            "https://www.youtube.com/youtubei/v1/player",
            body=load_asset("youtube_request_blocked.innertube.json.static"),
        )
        proxy_config = GenericProxyConfig(
            http_url="http://localhost:8080",
            https_url="http://localhost:8080",
        )

        with self.assertRaises(RequestBlocked) as cm:
            YouTubeTranscriptApi(proxy_config=proxy_config).fetch("Njp5uhTorCo")

        self.assertEqual(len(httpretty.latest_requests()), 2)
        self.assertEqual(cm.exception._proxy_config, proxy_config)
        self.assertIn("YouTube is blocking your requests", str(cm.exception))

    @pytest.mark.skip(
        reason="This test is temporarily disabled because cookie auth is currently not "
        "working due to YouTube changes."
    )
    def test_fetch__with_cookies(self):
        cookie_path = get_asset_path("example_cookies.txt")
        transcript = YouTubeTranscriptApi(cookie_path=cookie_path).fetch("GJLlxj_dtq8")

        self.assertEqual(
            transcript,
            self.ref_transcript,
        )

    @pytest.mark.skip(
        reason="This test is temporarily disabled because cookie auth is currently not "
        "working due to YouTube changes."
    )
    def test_load_cookies(self):
        cookie_path = get_asset_path("example_cookies.txt")

        ytt_api = YouTubeTranscriptApi(cookie_path=cookie_path)

        session_cookies = ytt_api._fetcher._http_client.cookies
        self.assertEqual(
            {"TEST_FIELD": "TEST_VALUE"},
            requests.utils.dict_from_cookiejar(session_cookies),
        )

    @pytest.mark.skip(
        reason="This test is temporarily disabled because cookie auth is currently not "
        "working due to YouTube changes."
    )
    def test_load_cookies__bad_file_path(self):
        cookie_path = get_asset_path("nonexistent_cookies.txt")
        with self.assertRaises(CookiePathInvalid):
            YouTubeTranscriptApi(cookie_path=cookie_path)

    @pytest.mark.skip(
        reason="This test is temporarily disabled because cookie auth is currently not "
        "working due to YouTube changes."
    )
    def test_load_cookies__no_valid_cookies(self):
        cookie_path = get_asset_path("expired_example_cookies.txt")
        with self.assertRaises(CookieInvalid):
            YouTubeTranscriptApi(cookie_path=cookie_path)
