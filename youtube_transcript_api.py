#!./.venv/bin/python

import sys

import json

from pprint import pprint

from src.transcript_api import YouTubeTranscriptApi


if __name__ == '__main__':
    if sys.argv[1] == '--json':
        print(json.dumps(YouTubeTranscriptApi.get_transcripts(*sys.argv[2:], continue_after_error=True)[0]))
    else:
        pprint(YouTubeTranscriptApi.get_transcripts(*sys.argv[1:], continue_after_error=True)[0])
