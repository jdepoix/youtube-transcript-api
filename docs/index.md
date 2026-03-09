---
layout: default
title: Home
---

# YT Tools

A growing toolkit for working with YouTube transcripts — from quick one-off fetches to full watch-history analysis.

## What's in the box?

| Tool | What it does | API Key? |
|------|-------------|----------|
| **youtube-transcript-api** | Python library & CLI to fetch any video's transcript | No |
| **do_fetch.py** | Quick script — fetch a transcript and copy to clipboard | No |
| **YT Transcript (Menu Bar App)** | macOS menu bar app for instant transcript access | No |
| **YT History Inspector** | Web app to analyze your YouTube watch history | Yes — Google OAuth |
| **Demo App** | Flask reference app combining all tools | Yes — Google OAuth |

## Quick start

### Fetch a transcript (no key needed)

```bash
pip install youtube-transcript-api
```

```python
from youtube_transcript_api import YouTubeTranscriptApi

api = YouTubeTranscriptApi()
transcript = api.fetch("dQw4w9WgXcQ")

for snippet in transcript:
    print(snippet.text)
```

Or from the CLI:

```bash
youtube_transcript_api dQw4w9WgXcQ
```

### Install the macOS menu bar app (no key needed)

```bash
curl -fsSL https://api.github.com/repos/kamir/youtube-transcript-api/contents/tools/install.sh?ref=kamir/yt-tools -H 'Accept: application/vnd.github.raw' | bash
```

### Run the History Inspector (OAuth key required)

See the [Authentication Guide](authentication) first, then:

```bash
# with Docker
docker compose up

# or directly
cd demo_app && python app.py
```

---

Next: [Getting Started](getting-started) | [Authentication Guide](authentication)
