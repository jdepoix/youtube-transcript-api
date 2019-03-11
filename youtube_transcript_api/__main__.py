import sys

import json

from pprint import pprint

import logging

import argparse

from ._api import YouTubeTranscriptApi


def parse_args(args):
    parser = argparse.ArgumentParser(
        description=(
            'This is an python API which allows you to get the transcripts/subtitles for a given YouTube video. '
            'It also works for automatically generated subtitles and it does not require a headless browser, like '
            'other selenium based solutions do!'
        )
    )
    parser.add_argument('video_ids', nargs='*', type=str, help='List of YouTube video IDs.')
    parser.add_argument(
        '--languages',
        nargs='*',
        default=[],
        type=str,
        help=(
            'A list of language codes in a descending priority. For example, if this is set to "de en" it will first '
            'try to fetch the german transcript (de) and then fetch the english transcipt (en) if it fails to do so. '
            'As I can\'t provide a complete list of all working language codes with full certainty, you may have to '
            'play around with the language codes a bit, to find the one which is working for you!'
        ),
    )
    parser.add_argument(
        '--json',
        action='store_const',
        const=True,
        default=False,
        help='If this flag is set the output will be JSON formatted.',
    )

    return parser.parse_args(args)


def main():
    logging.basicConfig()

    parsed_args = parse_args(sys.argv[1:])
    transcripts, _ = YouTubeTranscriptApi.get_transcripts(
        parsed_args.video_ids,
        languages=parsed_args.languages,
        continue_after_error=True
    )

    if parsed_args.json:
        print(json.dumps(transcripts))
    else:
        pprint(transcripts)


if __name__ == '__main__':
    main()
