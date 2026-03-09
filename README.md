# YT Transcript -- macOS Menu Bar App

A native macOS menu bar app that grabs YouTube transcripts with one click and copies them to your clipboard.

Built on top of [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) by [@jdepoix](https://github.com/jdepoix).

## Install

**One-liner** (downloads the latest release and installs to `/Applications`):

```bash
curl -fsSL 'https://api.github.com/repos/kamir/youtube-transcript-api/contents/tools/install.sh?ref=kamir/yt-tools' -H 'Accept: application/vnd.github.raw' | bash
```

**From source:**

```bash
git clone https://github.com/kamir/youtube-transcript-api.git
cd youtube-transcript-api
git checkout kamir/yt-tools
tools/build.sh
tools/deploy.sh
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

## Lifecycle scripts

All scripts live in `tools/`. Run from the repo root.

| Script | What it does |
|--------|-------------|
| `tools/status.sh` | Show install, running, build, log, and history status |
| `tools/pull.sh` | Pull latest changes from remote |
| `tools/build.sh` | Clean build the .app bundle |
| `tools/deploy.sh` | Stop running instance, install to /Applications, launch |
| `tools/update.sh` | **Pull + build + deploy** (one command) |
| `tools/start.sh` | Launch the installed app |
| `tools/stop.sh` | Stop the running app |
| `tools/uninstall.sh` | Remove app, data, and logs |
| `tools/release.sh` | Build + package zip for a GitHub release |
| `tools/install.sh` | Remote install from latest GitHub release |

**Daily workflow** -- pull the latest and redeploy:

```bash
tools/update.sh
```

## Credits

- **[youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)** -- the Python library that powers transcript fetching
- **[rumps](https://github.com/jaredks/rumps)** -- Ridiculously Uncomplicated macOS Python Statusbar apps
