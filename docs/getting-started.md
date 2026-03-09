---
layout: default
title: Getting Started
---

# Getting Started

## Prerequisites

- Python 3.8 or later
- macOS (for the menu bar app)
- A Google Cloud project (only if you want to use the History Inspector)

## Installation

### Core library

```bash
pip install youtube-transcript-api
```

### From source (all tools)

```bash
git clone https://github.com/kamir/youtube-transcript-api.git
cd youtube-transcript-api
git checkout kamir/yt-tools
pip install -e ".[dev]"
```

## Usage overview

### 1. Fetch a single transcript

No API key needed. Works out of the box.

```python
from youtube_transcript_api import YouTubeTranscriptApi

api = YouTubeTranscriptApi()
transcript = api.fetch("VIDEO_ID", languages=["en"])

full_text = "\n".join(snippet.text for snippet in transcript)
print(full_text)
```

**Language selection:** Pass a list of preferred languages. The API will try each in order and fall back automatically.

```python
# Prefer German, fall back to English
transcript = api.fetch("VIDEO_ID", languages=["de", "en"])
```

### 2. CLI usage

```bash
# Fetch transcript as plain text
youtube_transcript_api VIDEO_ID

# Fetch in JSON format
youtube_transcript_api VIDEO_ID --format json

# Specify language
youtube_transcript_api VIDEO_ID --languages en de
```

### 3. Quick clipboard copy (macOS)

Edit the `video_id` in `do_fetch.py` and run:

```bash
python3 do_fetch.py
```

The transcript is printed and copied to your clipboard.

### 4. Menu bar app

See the [Menu Bar App](menubar-app) page.

### 5. History Inspector

Requires a Google OAuth client secret. See [Authentication](authentication), then [History Inspector](history-inspector).

---

Next: [Authentication Guide](authentication)
