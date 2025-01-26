import sys

import logging

from ._cli import YouTubeTranscriptCli


def main():               #main function of program
    logging.basicConfig()

    print(YouTubeTranscriptCli(sys.argv[1:]).run())


if __name__ == "__main__":
    main()
