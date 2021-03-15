import json
from mock import MagicMock
from unittest import TestCase

from youtube_transcript_api.formatters import (
    Formatter,
    JSONFormatter,
    TextFormatter,
    WebVTTFormatter
)


class TestFormatters(TestCase):
    def setUp(self):
        self.transcript = [
            {'text': 'Test line 1', 'start': 0.0, 'duration': 1.50},
            {'text': 'line between', 'start': 1.5, 'duration': 2.0},
            {'text': 'testing the end line', 'start': 2.5, 'duration': 3.25}
        ]
    
    def test_base_formatter_valid_type(self):
        with self.assertRaises(TypeError) as err:
            Formatter({"test": []})
        expected_err = "'transcript' must be of type: List"
        self.assertEqual(expected_err, str(err.exception))
    
    def test_base_formatter_format_call(self):
        with self.assertRaises(NotImplementedError) as err:
            Formatter(self.transcript).format()
        
        expected_err = "A subclass of Formatter must implement their own " \
            ".format() method."
        self.assertEqual(expected_err, str(err.exception))

    def test_webvtt_formatter_starting(self):
        content = WebVTTFormatter(self.transcript).format()
        lines = content.split('\n')
        # test starting lines
        self.assertEqual(lines[0], "WEBVTT")
        self.assertEqual(lines[1], "")
    
    def test_webvtt_formatter_ending(self):
        content = WebVTTFormatter(self.transcript).format()
        lines = content.split('\n')
        # test ending lines
        self.assertEqual(lines[-2], self.transcript[-1]['text'])
        self.assertEqual(lines[-1], "")
    
    def test_json_formatter(self):
        content = JSONFormatter(self.transcript).format()
        self.assertEqual(json.loads(content), self.transcript)

    def test_text_formatter(self):
        content = TextFormatter(self.transcript).format()
        lines = content.split('\n')
        self.assertEqual(lines[0], self.transcript[0]["text"])
        self.assertEqual(lines[-1], self.transcript[-1]["text"])
