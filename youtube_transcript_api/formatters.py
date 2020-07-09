from abc import ABC
from abc import abstractclassmethod
from collections import defaultdict
import json
import re


def parse_timecode(time):
    """Converts a `time` into a formatted transcript timecode.

    :param time: a float representing time in seconds.
    :type time: float
    :return: a string formatted as a timecode, 'HH:MM:SS,MS'
    :rtype str

    :example:
    >>> parse_timecode(6.93)
    '00:00:06,930'
    """
    time = float(time)
    hours, mins, secs = (
        str(int(time)//3600).rjust(2, '0'),
        str(int(time)//60).rjust(2, '0'),
        str(int(time)%60).rjust(2, '0'),
    )
    ms = str(int(round((time - int(time))*1000, 2))).rjust(3, '0')
    return f"{hours}:{mins}:{secs},{ms}"


class TranscriptFormatter(ABC):
    """Abstract Base TranscriptFormatter class

    This class should be inherited from to create additional
     custom transcript formatters.
    """
    HTML_TAG_REGEX = re.compile(r'<[^>]*>', re.IGNORECASE)
    DELIMITER = ''

    @classmethod
    def combine(cls, transcripts):
        """Subclass may override this class method.

        Default behavior of this method will ''.join() the str() 
         of each transcript in transcripts.

        :param transcripts: a list of many transcripts
        :type transcript_data: list[<formatted transcript>, ...]
        :return: A string joined on the `cls.DELIMITER` to combine transcripts
        :rtype: str
        """
        return cls.DELIMITER.join(
                str(transcript) for transcript in transcripts)

    @abstractclassmethod
    def format(cls, transcript_data):
        """Any subclass must implement this format class method.

        :param transcript_data: a list of transcripts, 1 or more.
        :type transcript_data: list[list[dict], list[dict]]
        :return: A list where each item is an individual transcript
         as a string.
        :rtype: list[str]
        """
        pass


class JSONTranscriptFormatter(TranscriptFormatter):
    """Formatter for outputting JSON data"""
    DELIMITER = ','

    @classmethod
    def combine(cls, transcripts):
        return json.dumps(transcripts)

    @classmethod
    def format(cls, transcript_data):
        return transcript_data


class TextTranscriptFormatter(TranscriptFormatter):
    """Formatter for outputting a Plain Text Format

    Converts the fetched transcript data into separated lines of
     plain text separated by newline breaks (\n) with no timecodes.
    """
    DELIMITER = '\n\n'

    @classmethod
    def format(cls, transcript_data):
        return '{}\n'.format('\n'.join(
                    line['text']for line in transcript_data))


class SRTTranscriptFormatter(TranscriptFormatter):
    """Formatter for outputting the SRT Format

    Converts the fetched transcript data into a simple .srt file format.
    """
    DELIMITER = '\n\n'

    @classmethod
    def format(cls, transcript_data):
        output = []
        for frame, item in enumerate(transcript_data, start=1):
            start_time = float(item.get('start'))
            duration = float(item.get('dur', '0.0'))

            end_time = parse_timecode(start_time + duration)
            start_time = parse_timecode(start_time)

            output.append("{frame}\n".format(frame=frame))
            output.append("{start_time} --> {end_time}\n".format(
                start_time=start_time, end_time=end_time))
            output.append("{text}".format(text=item.get('text')))
            if frame < len(transcript_data):
                output.append('\n\n')

        return '{}\n'.format(''.join(output))


class TranscriptFormatterFactory:
    """A Transcript Class Factory

    Allows for adding additional custom Transcript classes for the API
    to use. Custom Transcript classes must inherit from the
    TranscriptFormatter abstract base class.
    """
    def __init__(self):
        self._formatters = defaultdict(JSONTranscriptFormatter)

    def add_formatter(self, name, formatter_class):
        """Allows for creating additional transcript formatters.


        :param name: a name given to the `formatter_class`
        :type name: str
        :param formatter_class: a subclass of TranscriptFormatter
        :type formatter_class: class
        :rtype None
        """
        if not issubclass(formatter_class, TranscriptFormatter):
            raise TypeError(
                f'{formatter_class} must be a subclass of TranscriptFormatter')
        self._formatters.update({name: formatter_class})

    def add_formatters(self, formatters_dict):
        """Allow creation of multiple transcript formatters at a time.

        :param formatters_dict: key(s) are the string name to be given
         to the formatter class, value for each key should be a subclass
         of TranscriptFormatter.
        :type formatters_dict: dict
        :rtype None
        """
        for name, formatter_class in formatters_dict.items():
            self.add_formatter(name, formatter_class)

    def get_formatter(self, name):
        """Retrieve a formatter class by its assigned name.

        :param name: the string name given to the formatter class.
        :type name: str
        :return: a subclass of `TranscriptFormatter`
        """
        return self._formatters[name]


formats = TranscriptFormatterFactory()
formats.add_formatters({
    'json': JSONTranscriptFormatter,
    'srt': SRTTranscriptFormatter,
    'text': TextTranscriptFormatter
})
