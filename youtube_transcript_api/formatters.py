import json


class Formatter(object):
    """Formatter should be used as an abstract base class.
    
    Formatter classes should inherit from this class and implement
    their own .format() method which should return a string. A 
    transcript is represented by a List of Dictionary items.

    :param transcript: list representing 1 or more transcripts
    :type transcript: list
    """
    def __init__(self, transcript):
        if not isinstance(transcript, list):
            raise TypeError("'transcript' must be of type: List")

        self._transcript = transcript
    
    def format(self, **kwargs):
        raise NotImplementedError('A subclass of Formatter must implement ' \
            'their own .format() method.')


class JSONFormatter(Formatter):
    def format(self, **kwargs):
        """Converts a transcript into a JSON string.

        :return: A JSON string representation of the transcript.'
        :rtype str
        """
        return json.dumps(self._transcript, **kwargs)


class TextFormatter(Formatter):
    def format(self, **kwargs):
        """Converts a transcript into plain text with no timestamps.

        :return: all transcript text lines separated by newline breaks.'
        :rtype str
        """
        return "\n".join(line['text'] for line in self._transcript)


class WebVTTFormatter(Formatter):
    def _seconds_to_timestamp(self, time):
        """Helper that converts `time` into a transcript cue timestamp.

        :reference: https://www.w3.org/TR/webvtt1/#webvtt-timestamp

        :param time: a float representing time in seconds.
        :type time: float
        :return: a string formatted as a cue timestamp, 'HH:MM:SS.MS'
        :rtype str
        :example:
        >>> self._seconds_to_timestamp(6.93)
        '00:00:06.930'
        """
        time = float(time)
        hours, mins, secs = (
            int(time) // 3600,
            int(time) // 60,
            int(time) % 60,
        )
        ms = int(round((time - int(time))*1000, 2))
        return "{:02d}:{:02d}:{:02d}.{:03d}".format(hours, mins, secs, ms)
    
    def format(self, **kwargs):
        """A basic implementation of WEBVTT formatting.

        :reference: https://www.w3.org/TR/webvtt1/#introduction-caption
        """
        lines = []
        for i, line in enumerate(self._transcript):
            if i < len(self._transcript)-1:
                # Looks ahead, use next start time since duration value
                # would create an overlap between start times.
                time_text = "{} --> {}".format(
                    self._seconds_to_timestamp(line['start']),
                    self._seconds_to_timestamp(self._transcript[i+1]['start'])
                )
            else:
                # Reached the end, cannot look ahead, use duration now.
                duration = line['start'] + line['duration']
                time_text = "{} --> {}".format(
                    self._seconds_to_timestamp(line['start']),
                    self._seconds_to_timestamp(duration)
                )
            lines.append("{}\n{}".format(time_text, line['text']))
        
        return "WEBVTT\n\n" + "\n\n".join(lines) + "\n"
