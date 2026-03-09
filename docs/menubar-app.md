---
layout: default
title: Menu Bar App
---

# YT Transcript — macOS Menu Bar App

A lightweight macOS menu bar app for fetching YouTube transcripts with one click. No API key needed.

## Features

- Lives in your menu bar with a YouTube-red icon
- Paste a video URL or ID, get the transcript
- Language selection (prefers English, with fallback options)
- Auto-copies transcript to clipboard
- Keeps a history of your last 20 transcripts
- Re-copy any previous transcript from the menu

## Installation

### One-liner install (recommended)

```bash
curl -fsSL https://api.github.com/repos/kamir/youtube-transcript-api/contents/tools/install.sh?ref=kamir/yt-tools -H 'Accept: application/vnd.github.raw' | bash
```

This downloads the latest release, installs to `/Applications`, and launches the app.

### Build from source

```bash
git clone https://github.com/kamir/youtube-transcript-api.git
cd youtube-transcript-api
git checkout kamir/yt-tools
pip install rumps pyobjc-framework-Cocoa defusedxml requests py2app
python3 setup_app.py py2app
```

The built app will be in `dist/YT Transcript.app`. Move it to `/Applications`.

## Usage

1. Click the YT icon in your menu bar
2. Select **Fetch Transcript...**
3. Paste a YouTube URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`) or just the video ID
4. Choose a language if multiple are available
5. The transcript is copied to your clipboard

## History

The app remembers your last 20 transcripts. Access them from the menu bar dropdown — click any entry to re-copy it to your clipboard.

## Logs

If something goes wrong, check the log file:

```
~/Library/Logs/YTTranscript.log
```

## Uninstalling

```bash
rm -rf "/Applications/YT Transcript.app"
rm -rf ~/Library/Application\ Support/YTTranscript
```

---

Back: [Getting Started](getting-started) | Next: [History Inspector](history-inspector)
