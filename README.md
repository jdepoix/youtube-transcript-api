# YT Transcript -- macOS Menu Bar App

A native macOS menu bar app that grabs YouTube transcripts with one click and copies them to your clipboard.

Built on top of [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) by [@jdepoix](https://github.com/jdepoix).

## Install

**One-liner** (downloads the latest release and installs to `/Applications`):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/kamir/youtube-transcript-api/kamir/yt-tools/tools/install.sh)"
```

**Manual** (build from source):

```bash
git clone https://github.com/kamir/youtube-transcript-api.git
cd youtube-transcript-api
git checkout kamir/yt-tools
pip3 install rumps pyobjc-framework-Cocoa defusedxml requests py2app
python3 setup_app.py py2app
cp -R "dist/YT Transcript.app" /Applications/
open "/Applications/YT Transcript.app"
```

## How it works

1. Click the YouTube icon in your menu bar
2. Enter a video ID or paste a full YouTube URL
3. The video opens in your browser for preview
4. The transcript is fetched and copied to your clipboard
5. A confirmation dialog shows the result with two options:
   - **Close** -- keep the clipboard content
   - **Trash** -- clear the clipboard (plays the macOS trash sound)

## Features

| Feature | Details |
|---------|---------|
| Language fallback | If English isn't available, offers the original language or an English translation -- you choose |
| Language flags | Shows the flag of the transcript language in status, notifications, and history |
| Clipboard feedback | Menu bar shows a clipboard icon after fetch; dialog lets you keep or discard |
| History | Last 20 transcripts stored; re-copy any entry from the History submenu |
| Logging | All activity logged to `~/Library/Logs/YTTranscript.log` |

## Release (maintainer)

```bash
tools/release.sh 1.1.0
```

This builds the `.app`, zips it, and prints the `git tag` + `gh release create` commands to run.

## Rebuild after changes

```bash
rm -rf build dist
python3 setup_app.py py2app
cp -R "dist/YT Transcript.app" /Applications/
```

## Credits

- **[youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)** -- the Python library that powers transcript fetching
- **[rumps](https://github.com/jaredks/rumps)** -- Ridiculously Uncomplicated macOS Python Statusbar apps
