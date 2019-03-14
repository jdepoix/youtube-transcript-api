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

        parsed_args = YouTubeTranscriptCli('v1 v2 --languages de en --json'.split())._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, ['de', 'en'])

        parsed_args = YouTubeTranscriptCli(' --json v1 v2 --languages de en'.split())._parse_args()
        self.assertEqual(parsed_args.video_ids, ['v1', 'v2'])
        self.assertEqual(parsed_args.json, True)
        self.assertEqual(parsed_args.languages, ['de', 'en'])

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

    def test_run(self):
        YouTubeTranscriptApi.get_transcripts = MagicMock(return_value=([], []))
        YouTubeTranscriptCli('v1 v2 --languages de en'.split()).run()

        YouTubeTranscriptApi.get_transcripts.assert_called_once_with(
            ['v1', 'v2'],
            languages=['de', 'en'],
            continue_after_error=True
        )

    def test_run__json_output(self):
        YouTubeTranscriptApi.get_transcripts = MagicMock(return_value=([{'boolean': True}], []))
        output = YouTubeTranscriptCli('v1 v2 --languages de en --json'.split()).run()

        # will fail if output is not valid json
        json.loads(output)
