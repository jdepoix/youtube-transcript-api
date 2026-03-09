---
layout: default
title: Authentication Guide
---

# Authentication Guide

## Do I need an API key?

**Most features work without any key.** The core transcript-fetching library scrapes YouTube directly — no Google account, no API key, no OAuth.

You only need credentials if you want to use the **History Inspector** or **Demo App**, which access your personal YouTube watch history via the Google YouTube Data API v3.

## Overview

| Feature | Auth method | Key needed? |
|---------|------------|-------------|
| Fetch transcripts (library, CLI, script) | None | No |
| Menu bar app | None | No |
| History Inspector / Demo App | Google OAuth 2.0 | Yes — `client_secret.json` |

---

## Setting up Google OAuth credentials

Follow these steps to create a `client_secret.json` for the History Inspector.

### Step 1: Create a Google Cloud project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** (top bar) then **New Project**
3. Name it something like `youtube-transcript-tools` and click **Create**
4. Make sure your new project is selected in the top bar

### Step 2: Enable the YouTube Data API

1. Go to **APIs & Services > Library**
2. Search for **YouTube Data API v3**
3. Click on it, then click **Enable**

### Step 3: Configure the OAuth consent screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** (unless you have a Google Workspace org) and click **Create**
3. Fill in the required fields:
   - **App name:** `YT History Inspector` (or any name you like)
   - **User support email:** your email
   - **Developer contact:** your email
4. Click **Save and Continue**
5. On the **Scopes** page, click **Add or Remove Scopes**, then add:
   - `https://www.googleapis.com/auth/youtube.readonly`
6. Click **Save and Continue** through the remaining steps
7. On the **Test users** page, add your Google account email
8. Click **Save and Continue**, then **Back to Dashboard**

> **Note:** While the app is in "Testing" mode, only the test users you listed can log in. This is fine for personal use.

### Step 4: Create OAuth client credentials

1. Go to **APIs & Services > Credentials**
2. Click **+ Create Credentials > OAuth client ID**
3. Application type: **Web application**
4. Name: `YT History Inspector` (or any name)
5. Under **Authorized redirect URIs**, add:
   - `http://localhost:8080/auth/callback`
   - (Add your production URL if deploying remotely)
6. Click **Create**
7. Click **Download JSON** on the confirmation dialog
8. Save the downloaded file as `client_secret.json` in the project root

### Step 5: Place the credentials file

```bash
# Move the downloaded file to the project root
mv ~/Downloads/client_id_*.json ./client_secret.json
```

The file should look like this (your values will differ):

```json
{
  "web": {
    "client_id": "123456789-xxxx.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_secret": "GOCSPX-your-secret-here",
    "redirect_uris": ["http://localhost:8080/auth/callback"]
  }
}
```

### Step 6: Configure environment variables (optional)

The defaults work for local development. Override them if needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `YTHI_CLIENT_SECRET` | `client_secret.json` | Path to your OAuth credentials file |
| `YTHI_BASE_URL` | `http://localhost:8080` | Base URL for OAuth redirect |
| `YTHI_DB_PATH` | `data/app.db` | SQLite database path |
| `YTHI_DATA_DIR` | `data` | Data directory |
| `YTHI_FLASK_SECRET` | `dev-secret` | Flask session secret (change in production!) |
| `YTHI_HISTORY_PLAYLIST_ID` | `HL` | YouTube history playlist ID |

Example:

```bash
export YTHI_CLIENT_SECRET="/path/to/client_secret.json"
export YTHI_FLASK_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

### Using Docker

When running with Docker Compose, mount the credentials file read-only:

```bash
# Place client_secret.json in the project root, then:
docker compose up
```

The `docker-compose.yml` is preconfigured to mount `./client_secret.json` into the container.

---

## Security best practices

- **Never commit `client_secret.json` to git.** It is already in `.gitignore`.
- **Use a strong `YTHI_FLASK_SECRET`** in production (not the default `dev-secret`).
- The OAuth scope is **read-only** — the app cannot modify your YouTube account.
- Tokens are stored locally in the SQLite database. Keep `data/app.db` secure.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "redirect_uri_mismatch" error | Make sure `http://localhost:8080/auth/callback` is listed in your Google Cloud OAuth redirect URIs |
| "Access blocked: app not verified" | Add your email as a test user in the OAuth consent screen |
| "client_secret.json not found" | Set `YTHI_CLIENT_SECRET` to the correct path, or place the file in the project root |
| Token expired | The app auto-refreshes tokens. If it fails, delete `data/app.db` and re-authenticate |

---

Next: [Menu Bar App](menubar-app) | [History Inspector](history-inspector)
