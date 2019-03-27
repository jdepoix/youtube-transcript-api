from unittest import TestCase
from mock import MagicMock

import json

from youtube_transcript_api._cli import YouTubeTranscriptCli, YouTubeTranscriptApi


class TestYouTubeTranscriptCli(TestCase):
    def test_argument_parsing(self):
        parsed_args = YouTubeTranscriptCli('v1 v2 --json --languages de en'.split())._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, ['de', 'en'])
        self.assertEqual(parsed_args.http_proxy, '')
        self.assertEqual(parsed_args.https_proxy, '')

        parsed_args = YouTubeTranscriptCli('v1 v2 --languages de en --json'.split())._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, ['de', 'en'])
        self.assertEqual(parsed_args.http_proxy, '')
        self.assertEqual(parsed_args.https_proxy, '')

        parsed_args = YouTubeTranscriptCli(' --json v1 v2 --languages de en'.split())._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, ['de', 'en'])
        self.assertEqual(parsed_args.http_proxy, '')
        self.assertEqual(parsed_args.https_proxy, '')

        parsed_args = YouTubeTranscriptCli(
            'v1 v2 --languages de en --json --http-proxy http://user:pass@domain:port --https-proxy https://user:pass@domain:port'.split()
        )._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, ['de', 'en'])
        self.assertEqual(parsed_args.http_proxy, 'http://user:pass@domain:port')
        self.assertEqual(parsed_args.https_proxy, 'https://user:pass@domain:port')

        parsed_args = YouTubeTranscriptCli(
            'v1 v2 --languages de en --json --http-proxy http://user:pass@domain:port'.split()
        )._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, ['de', 'en'])
        self.assertEqual(parsed_args.http_proxy, 'http://user:pass@domain:port')
        self.assertEqual(parsed_args.https_proxy, '')

        parsed_args = YouTubeTranscriptCli(
            'v1 v2 --languages de en --json --https-proxy https://user:pass@domain:port'.split()
        )._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, ['de', 'en'])
        self.assertEqual(parsed_args.https_proxy, 'https://user:pass@domain:port')
        self.assertEqual(parsed_args.http_proxy, '')

    def test_argument_parsing__only_video_ids(self):
        parsed_args = YouTubeTranscriptCli('v1 v2'.split())._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, False)
        self.assertEqual(parsed_args.languages, [])

    def test_argument_parsing__fail_without_video_ids(self):
        with self.assertRaises(SystemExit):
            YouTubeTranscriptCli('--json'.split())._parse_args()

    def test_argument_parsing__json(self):
        parsed_args = YouTubeTranscriptCli('v1 v2 --json'.split())._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, [])

        parsed_args = YouTubeTranscriptCli('--json v1 v2'.split())._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, [])

    def test_argument_parsing__languages(self):
        parsed_args = YouTubeTranscriptCli('v1 v2 --languages de en'.split())._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, False)
        self.assertEqual(parsed_args.languages, ['de', 'en'])

    def test_argument_parsing__proxies(self):
        parsed_args = YouTubeTranscriptCli(
            'v1 v2 --http-proxy http://user:pass@domain:port'.split()
        )._parse_args()
        self.assertEqual(parsed_args.http_proxy, 'http://user:pass@domain:port')

        parsed_args = YouTubeTranscriptCli(
            'v1 v2 --https-proxy https://user:pass@domain:port'.split()
        )._parse_args()
        self.assertEqual(parsed_args.https_proxy, 'https://user:pass@domain:port')

        parsed_args = YouTubeTranscriptCli(
            'v1 v2 --http-proxy http://user:pass@domain:port --https-proxy https://user:pass@domain:port'.split()
        )._parse_args()
        self.assertEqual(parsed_args.http_proxy, 'http://user:pass@domain:port')
        self.assertEqual(parsed_args.https_proxy, 'https://user:pass@domain:port')

        parsed_args = YouTubeTranscriptCli(
            'v1 v2'.split()
        )._parse_args()
        self.assertEqual(parsed_args.http_proxy, '')
        self.assertEqual(parsed_args.https_proxy, '')

    def test_run(self):
        YouTubeTranscriptApi.get_transcripts = MagicMock(return_value=([], []))
        YouTubeTranscriptCli('v1 v2 --languages de en'.split()).run()

        YouTubeTranscriptApi.get_transcripts.assert_called_once_with(
            ['v1', 'v2'],
            languages=['de', 'en'],
            continue_after_error=True,
            proxies=None
        )

    def test_run__json_output(self):
        YouTubeTranscriptApi.get_transcripts = MagicMock(return_value=([{'boolean': True}], []))
        output = YouTubeTranscriptCli('v1 v2 --languages de en --json'.split()).run()

        # will fail if output is not valid json
        json.loads(output)

    def test_run__proxies(self):
        YouTubeTranscriptApi.get_transcripts = MagicMock(return_value=([], []))
        YouTubeTranscriptCli(
            'v1 v2 --languages de en --http-proxy http://user:pass@domain:port --https-proxy https://user:pass@domain:port'.split()).run()

        YouTubeTranscriptApi.get_transcripts.assert_called_once_with(
            ['v1', 'v2'],
            languages=['de', 'en'],
            continue_after_error=True,
            proxies={'http': 'http://user:pass@domain:port', 'https': 'https://user:pass@domain:port'}
        )
