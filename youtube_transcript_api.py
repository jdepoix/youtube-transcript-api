#!/usr/bin/python

import sys

import json

from pprint import pprint

import logging

from src.transcript_api import YouTubeTranscriptApi


if __name__ == '__main__':
    logging.basicConfig()

    if sys.argv[1] == '--json':
        print(json.dumps(YouTubeTranscriptApi.get_transcripts(sys.argv[2:], continue_after_error=True)[0]))
    else:
        pprint(YouTubeTranscriptApi.get_transcripts(sys.argv[1:], continue_after_error=True)[0])
