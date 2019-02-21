import sys

import json

from pprint import pprint

import logging

from ._api import YouTubeTranscriptApi


def main():
    logging.basicConfig()

    if len(sys.argv) <= 1:
        print('No YouTube video id was found')
    elif sys.argv[1] == '--json':
        print(json.dumps(YouTubeTranscriptApi.get_transcripts(sys.argv[2:], continue_after_error=True)[0]))
    else:
        pprint(YouTubeTranscriptApi.get_transcripts(sys.argv[1:], continue_after_error=True)[0])


if __name__ == '__main__':
    main()
