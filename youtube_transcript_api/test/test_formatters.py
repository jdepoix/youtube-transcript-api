from unittest import TestCase
from mock import MagicMock
import json

from youtube_transcript_api.formatters import (
    JSONTranscriptFormatter,
    parse_timecode,
    SRTTranscriptFormatter,
    TextTranscriptFormatter,
    TranscriptFormatter,
    TranscriptFormatterFactory
)


class TestTranscriptFormatters(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.transcript = [
            {
                'text': 'Hey, this is just a test',
                'start': 0.0,
                'duration': 1.54
            },
            {
                'text': 'this is not the original transcript',
                'start': 1.54,
                'duration': 4.16
            },
            {
                'text': 'just something shorter, I made up for testing',
                'start': 5.7,
                'duration': 3.239
            }
        ]

    def test_base_formatter_combine(self):
        expecting = ''.join([str(line) for line in self.transcript])

        self.assertEqual(
            TranscriptFormatter.combine(self.transcript),
            expecting
        )

    def test_base_format_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            TranscriptFormatter.format(self.transcript)

    def test_text_formatter_format(self):
        text = '\n'.join([line.get('text') for line in self.transcript])
        text_fmt = TextTranscriptFormatter.format(self.transcript)
        self.assertIn(text + '\n', text_fmt)

    def test_srt_formatter_format(self):
        start = self.transcript[0].get('start')
        duration = self.transcript[0].get('duration')
        srt_fmt = SRTTranscriptFormatter.format(self.transcript)
        self.assertIn('{start} --> {end}'.format(
                start=parse_timecode(start),
                end=parse_timecode(start+duration)
            ), srt_fmt)

    def test_json_formatter_format(self):
        json_fmt = JSONTranscriptFormatter.format(self.transcript)
        self.assertIsInstance(json.dumps(json_fmt), str)

    def test_invalid_parse_timecode(self):
        start_time = 'not_float'

        with self.assertRaises(ValueError):
            parse_timecode(start_time)

    def test_valid_parse_timecode(self):
        start_time = 0.0
        end_time = 5.20

        self.assertEqual(
            parse_timecode(start_time),
            '00:00:00,000'
        )

        self.assertEqual(
            parse_timecode(end_time),
            '00:00:05,200'
        )

    def test_formatter_factory_valid_single_add(self):
        factory = TranscriptFormatterFactory()
        factory.add_formatter('json', JSONTranscriptFormatter)

        self.assertDictEqual(
            getattr(factory, '_formatters'),
            {'json': JSONTranscriptFormatter}
        )

    def test_formatter_factory_invalid_single_add(self):
        factory = TranscriptFormatterFactory()

        with self.assertRaises(TypeError):
            factory.add_formatter('magic', MagicMock)
