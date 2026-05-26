#!/usr/bin/env python3
"""Fetch a YouTube transcript from a video URL or ID."""

import argparse
import re
import sys

from youtube_transcript_api import FetchedTranscript, YouTubeTranscriptApi

PARAGRAPH_GAP_SECONDS = 2.0


def extract_video_id(value: str) -> str:
    value = value.strip()

    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)

    raise ValueError(
        "Could not find a video ID. Paste a full YouTube link or an 11-character video ID."
    )


def clean_transcript(transcript: FetchedTranscript) -> str:
    paragraphs = []
    current_words = []
    prev_end = None

    for snippet in transcript:
        text = snippet.text.replace("\u00a0", "").replace("\u200b", "").strip()
        if not text:
            continue

        if prev_end is not None:
            gap = snippet.start - prev_end
            if gap > PARAGRAPH_GAP_SECONDS:
                if current_words:
                    paragraphs.append(" ".join(current_words))
                    current_words = []

        current_words.append(text)
        prev_end = snippet.start + snippet.duration

    if current_words:
        paragraphs.append(" ".join(current_words))

    return "\n\n".join(re.sub(r"\s+", " ", para) for para in paragraphs)


def format_output(transcript: FetchedTranscript, video_id: str) -> str:
    body = clean_transcript(transcript)
    return (
        f"Source: https://www.youtube.com/watch?v={video_id}\n"
        f"Video ID: {video_id}\n"
        f"Language: {transcript.language}\n"
        f"\n"
        f"---\n"
        f"\n"
        f"{body}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch a YouTube transcript from a video URL or ID."
    )
    parser.add_argument(
        "video",
        help="YouTube URL or 11-character video ID",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Write transcript to FILE as UTF-8 (recommended instead of shell redirect)",
    )
    args = parser.parse_args()

    try:
        video_id = extract_video_id(args.video)
        transcript = YouTubeTranscriptApi().fetch(video_id)
        output = format_output(transcript, video_id)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as file:
                file.write(output)
        else:
            print(output)
        return 0
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
