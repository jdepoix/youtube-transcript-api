#!./.venv/bin/python

import sys

import json

from src.transcript_api import YouTubeTranscriptApi

if __name__ == '__main__':
    print(json.dumps(YouTubeTranscriptApi.get(*sys.argv[1:])))
