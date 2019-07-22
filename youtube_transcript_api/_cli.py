import json

import pprint

import argparse

from ._api import YouTubeTranscriptApi


class YouTubeTranscriptCli():
    def __init__(self, args):
        self._args = args

    def run(self):
        parsed_args = self._parse_args()

        proxies = None
        if parsed_args.http_proxy != '' or parsed_args.https_proxy != '':
            proxies = {"http": parsed_args.http_proxy, "https": parsed_args.https_proxy}

        transcripts, unretrievable_videos = YouTubeTranscriptApi.get_transcripts(
            parsed_args.video_ids,
            languages=parsed_args.languages,
            continue_after_error=True,
            proxies=proxies
        )

        return '\n\n'.join(
            [str(YouTubeTranscriptApi.CouldNotRetrieveTranscript(video_id)) for video_id in unretrievable_videos]
            + ([json.dumps(transcripts) if parsed_args.json else pprint.pformat(transcripts)] if transcripts else [])
        )

    def _parse_args(self):
        parser = argparse.ArgumentParser(
            description=(
                'This is an python API which allows you to get the transcripts/subtitles for a given YouTube video. '
                'It also works for automatically generated subtitles and it does not require a headless browser, like '
                'other selenium based solutions do!'
            )
        )
        parser.add_argument('video_ids', nargs='+', type=str, help='List of YouTube video IDs.')
        parser.add_argument(
            '--languages',
            nargs='*',
            default=[],
            type=str,
            help=(
                'A list of language codes in a descending priority. For example, if this is set to "de en" it will '
                'first try to fetch the german transcript (de) and then fetch the english transcipt (en) if it fails '
                'to do so. As I can\'t provide a complete list of all working language codes with full certainty, you '
                'may have to play around with the language codes a bit, to find the one which is working for you!'
            ),
        )
        parser.add_argument(
            '--json',
            action='store_const',
            const=True,
            default=False,
            help='If this flag is set the output will be JSON formatted.',
        )
        parser.add_argument(
            '--http-proxy', dest='http_proxy',
            default='', metavar='URL',
            help='Use the specified HTTP proxy.'
        )
        parser.add_argument(
            '--https-proxy', dest='https_proxy',
            default='', metavar='URL',
            help='Use the specified HTTPS proxy.'
        )

        return parser.parse_args(self._args)
