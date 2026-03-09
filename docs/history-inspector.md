---
layout: default
title: History Inspector
---

# YT History Inspector

A web app that syncs your YouTube watch history, fetches transcripts for each video, and gives you tools to explore and analyze what you've watched.

**Requires Google OAuth credentials.** See the [Authentication Guide](authentication) first.

## Features

- **OAuth login** — securely access your YouTube watch history (read-only)
- **History sync** — pull your recent watch history into a local SQLite database
- **Transcript fetching** — automatically fetch transcripts for synced videos
- **Timeline view** — browse your watch history with pagination and filtering
- **Word cloud** — visualize the most common words across your transcripts
- **Hide/show videos** — mark videos as irrelevant to clean up your view
- **Google Takeout import** — import full history from a Takeout export (ZIP/TAR.GZ)

## Running locally

### With Docker (recommended)

```bash
# 1. Place your client_secret.json in the project root (see Authentication Guide)
# 2. Start the app
docker compose up

# 3. Open http://localhost:8080
```

### Without Docker

```bash
# 1. Install dependencies
pip install flask google-auth google-auth-oauthlib google-api-python-client wordcloud pillow

# 2. Place your client_secret.json in the project root

# 3. Start the app
cd demo_app
python app.py

# 4. Open http://localhost:8080
```

## Walkthrough

1. Open `http://localhost:8080`
2. Click **Login with Google** — you'll be redirected to Google's consent screen
3. Authorize read-only access to your YouTube account
4. Click **Sync** to pull your watch history and fetch transcripts
5. Browse the **Timeline** to see your videos with transcripts
6. View the **Word Cloud** to see common themes across your transcripts

## Importing from Google Takeout

If you want your complete watch history (not just recent videos):

1. Go to [Google Takeout](https://takeout.google.com/)
2. Select only **YouTube and YouTube Music**
3. Click **Next step** and create the export
4. Download the archive when ready
5. Use the takeout import CLI:

```bash
python -m yt_history_inspector.takeout_import path/to/takeout.zip
```

## Architecture

```
demo_app/app.py              Flask web app (routes, templates)
yt_history_inspector/
  service.py                 HistoryInspector (main service facade)
  youtube_client.py          Google OAuth + YouTube API client
  db.py                      SQLite database layer
  transcripts.py             Transcript fetching integration
  timeline.py                Timeline builder
  wordclouds.py              Word cloud rendering
  takeout.py                 Google Takeout parser
  models.py                  Data models
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `YTHI_CLIENT_SECRET` | `client_secret.json` | Path to OAuth credentials |
| `YTHI_BASE_URL` | `http://localhost:8080` | Base URL for OAuth redirect |
| `YTHI_DB_PATH` | `data/app.db` | SQLite database path |
| `YTHI_DATA_DIR` | `data` | Data storage directory |
| `YTHI_FLASK_SECRET` | `dev-secret` | Flask session secret |
| `YTHI_HISTORY_PLAYLIST_ID` | `HL` | YouTube history playlist |

---

Back: [Menu Bar App](menubar-app) | Next: [Roadmap](roadmap)
