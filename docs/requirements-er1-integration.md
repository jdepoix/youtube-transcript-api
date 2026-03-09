---
layout: default
title: ER1 Integration — Requirements
---

# ER1 Integration — Requirements & Solution Plan

## Context

The project [audio-checklist-checker-py](https://github.com/kamir/my-ai-X) establishes a pattern for capturing audio impulses and pushing them into **ER1** — a personal knowledge/memory management system with a REST API. The workflow is:

```
Source (GDrive audio) → Metadata extraction → Whisper transcription
  → Local MEMORY folder → ER1 API upload → Post-processing (Gemini)
```

This document specifies how to bring that same pattern into the YouTube transcript toolkit, adding two new capabilities:

1. **Video Import to ER1** — select untracked YouTube videos and push their transcripts into ER1
2. **Impression Capture** — record a spoken voice note *about* a video, transcribe it, and bundle both the video transcript and the user's commentary as a single "impression" payload into ER1

---

## Terminology

| Term | Definition |
|------|-----------|
| **ER1** | External memory/knowledge API at `https://127.0.0.1:8081/upload_2` (local) or `https://onboarding.guide/upload_2` (remote) |
| **MEMORY folder** | Local directory `/Users/kamir/ER1/MEMORY-{YYYYMMDD_HHMMSS}/` holding source files, transcripts, tags, and post-processed outputs |
| **Untracked video** | A video present in the YT History Inspector database that has NOT yet been pushed to ER1 |
| **Impression** | A composite record: video transcript + user's spoken commentary about the video, bundled as one ER1 entry |
| **context_id** | ER1 user/org identifier: `107677460544181387647___mft` |

---

## Requirements

### R1 — ER1 Tracking State

**R1.1** The system MUST track which videos have been exported to ER1, separate from the existing `transcripts` and `transcript_jobs` tables.

**R1.2** A new `er1_exports` table (or equivalent) MUST store:
- `video_id` (FK to videos)
- `memory_id` (the MEMORY-{TIMESTAMP} folder name)
- `exported_at` (ISO timestamp)
- `export_type` ("transcript" or "impression")
- `er1_status` ("uploaded", "post_processed", "error")
- `tags` (comma-separated tags applied)

**R1.3** The timeline view MUST support a new filter: `not_in_er1=1` to show only videos not yet exported to ER1 (i.e., "untracked" from ER1's perspective).

---

### R2 — Video Selection & Import to ER1

**R2.1** The web UI (demo app) MUST provide a way to select one or more untracked videos for ER1 export, either:
- Individually from the video detail page (button: "Export to ER1")
- In bulk from the timeline view (checkboxes + "Export selected to ER1")

**R2.2** Before export, the user MUST be able to assign tags (free-text, comma-separated). Default tags: `["transcript.provided", "youtube"]`.

**R2.3** On export, the system MUST:
1. Create a local MEMORY folder: `/Users/kamir/ER1/MEMORY-{TIMESTAMP}/`
2. Write the transcript to `transcript_{TIMESTAMP}.txt`
3. Write tags to `tag.txt` (one tag per line)
4. Write video metadata to `metadata.json` (video_id, title, channel, URL, watched_at)
5. Upload to ER1 API via `POST /upload_2` with:
   - Header: `X-API-KEY`
   - Form fields: `context_id`, `content_type` = `"YouTube-Video-Transcript"`, `tags`
   - File attachment: `transcript_file_ext` = the transcript text file
6. Record the export in `er1_exports`

**R2.4** The menu bar app SHOULD also offer an "Export to ER1" option after fetching a transcript.

---

### R3 — Impression Capture (Voice + Video)

**R3.1** The web UI MUST provide a "Record Impression" action on the video detail page.

**R3.2** The impression workflow:
1. User views a video detail page (transcript already fetched)
2. User clicks "Record Impression"
3. User records a voice note via browser microphone (WebAudio API) or uploads an audio file
4. The system transcribes the voice note (using OpenAI Whisper, matching the audio-checklist-checker pattern)
5. The system creates a composite payload:
   - **Video transcript** — the YouTube transcript text
   - **User commentary** — the transcribed voice note
   - **Composite document** — both combined into a structured text file

**R3.3** The composite transcript file format:

```
=== VIDEO TRANSCRIPT ===
Title: {title}
Channel: {channel_title}
Video ID: {video_id}
URL: https://www.youtube.com/watch?v={video_id}
Language: {language_code}
Date watched: {watched_at}

{video_transcript_text}

=== USER IMPRESSION ===
Recorded: {impression_timestamp}
Language: {detected_language}

{user_voice_note_text}
```

**R3.4** On impression export, the system MUST:
1. Create a MEMORY folder: `/Users/kamir/ER1/MEMORY-{TIMESTAMP}/`
2. Copy the audio file (user's voice note) into the MEMORY folder
3. Write `transcript_{TIMESTAMP}.txt` (the composite document from R3.3)
4. Write `tag.txt` with tags: `["transcript.provided", "youtube", "impression", {channel_title}]`
5. Write `metadata.json` with video metadata + impression metadata
6. Upload to ER1 API with:
   - `content_type` = `"YouTube-Video-Impression"`
   - `audio_data_ext` = the user's voice note audio file
   - `transcript_file_ext` = the composite transcript
   - `tags` = combined tags
7. Record in `er1_exports` with `export_type = "impression"`

**R3.5** The menu bar app SHOULD support impression capture by opening a recording dialog after transcript fetch.

---

### R4 — Configuration

**R4.1** ER1 connection settings MUST be configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ER1_API_URL` | `https://127.0.0.1:8081/upload_2` | ER1 upload endpoint |
| `ER1_API_KEY` | *(required)* | API key for ER1 authentication |
| `ER1_CONTEXT_ID` | `107677460544181387647___mft` | ER1 user/org context |
| `ER1_MEMORY_PATH` | `/Users/kamir/ER1` | Local path for MEMORY folders |

**R4.2** Whisper model configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `large` | Whisper model size (tiny/base/small/medium/large) |

**R4.3** The `client_secret.json` and `ER1_API_KEY` MUST NOT be committed to git. Both must be listed in `.gitignore`.

---

### R5 — Post-Processing (Future)

**R5.1** The system SHOULD support tag-to-prompt mapping for post-processing via Gemini, following the `tag_promptKey_map` pattern from audio-checklist-checker.

**R5.2** Post-processing is out of scope for the initial implementation but the architecture MUST allow it to be added later (the MEMORY folder structure and tag.txt are the integration points).

---

### R6 — Tracking & Idempotency

**R6.1** The system MUST NOT re-export a video that has already been exported to ER1 (unless explicitly requested by the user).

**R6.2** The system MUST skip MEMORY folder creation if the folder already exists (idempotent).

**R6.3** Export history MUST be visible in the web UI — the video detail page shows export status and timestamp.

---

## Non-Requirements (Out of Scope)

- Post-processing with Gemini (deferred to R5, future work)
- Email draft generation from YouTube impressions
- Batch import of all YouTube history to ER1 (manual selection only for now)
- Browser extension integration

---

## Solution Plan

### Phase 1: ER1 Client Module

Create `yt_history_inspector/er1_client.py`:

```
er1_client.py
  ├── ER1Config (dataclass: api_url, api_key, context_id, memory_path)
  ├── create_memory_folder(timestamp) → Path
  ├── write_transcript(memory_path, text, timestamp) → Path
  ├── write_tags(memory_path, tags) → Path
  ├── write_metadata(memory_path, metadata_dict) → Path
  ├── upload_to_er1(config, memory_path, content_type, tags, audio_file=None) → response
  └── format_composite_transcript(video_meta, video_text, impression_text, impression_meta) → str
```

This module encapsulates the ER1 pattern so it can be reused across the web app and menu bar app.

### Phase 2: Database Extension

Add to `yt_history_inspector/db.py`:

```sql
CREATE TABLE IF NOT EXISTS er1_exports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id    TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    memory_id   TEXT NOT NULL,
    export_type TEXT NOT NULL DEFAULT 'transcript',
    tags        TEXT,
    er1_status  TEXT NOT NULL DEFAULT 'uploaded',
    exported_at TEXT NOT NULL,
    UNIQUE(video_id, export_type)
);
```

Add methods:
- `record_er1_export(video_id, memory_id, export_type, tags)`
- `get_er1_export(video_id)` → export record or None
- `fetch_videos_not_in_er1(limit)` → list of video_ids

### Phase 3: Service Layer

Extend `yt_history_inspector/service.py` (HistoryInspector):

```python
def export_to_er1(self, video_id, tags=None) → dict:
    """Export a video transcript to ER1. Returns {memory_id, status}."""

def record_impression(self, video_id, audio_path, tags=None) → dict:
    """Transcribe voice note, combine with video transcript, export to ER1."""

def er1_export_status(self, video_id) → dict | None:
    """Check if video has been exported to ER1."""
```

### Phase 4: Whisper Integration

Create `yt_history_inspector/whisper_transcriber.py`:

```python
class WhisperTranscriber:
    def __init__(self, model_name="large"):
        ...
    def transcribe(self, audio_path, language=None) → dict:
        """Returns {text, detected_language, model_name}"""
```

This wraps OpenAI Whisper, matching the audio-checklist-checker's `WhisperService` interface.

### Phase 5: Web UI Routes

Add to `demo_app/app.py`:

| Route | Method | Purpose |
|-------|--------|---------|
| `/er1/export/<video_id>` | POST | Export transcript to ER1 |
| `/er1/impression/<video_id>` | POST | Upload voice note + export impression |
| `/er1/status/<video_id>` | GET | Check ER1 export status |
| `/timeline?not_in_er1=1` | GET | Filter untracked videos |

Add to templates:
- `video.html`: "Export to ER1" button, "Record Impression" button, ER1 status badge
- `timeline.html`: "Not in ER1" filter checkbox, ER1 status indicator per video

### Phase 6: Menu Bar App Extension

Add to `yt_menubar.py`:
- "Export to ER1" menu item (appears after transcript fetch)
- "Record Impression" menu item (opens audio recording dialog)
- ER1 status indicator in history entries

### Phase 7: Documentation

Update `docs/`:
- New page: `er1-integration.md` — setup guide, usage, configuration
- Update `authentication.md` — add ER1 API key setup
- Update `roadmap.md` — mark ER1 integration items as planned/done

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Menu Bar App │  │  Web App     │  │  CLI              │  │
│  │  (yt_menubar) │  │  (demo_app)  │  │  (future)         │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────────┘  │
│         │                 │                   │              │
│  ┌──────┴─────────────────┴───────────────────┴───────────┐  │
│  │              HistoryInspector (service.py)              │  │
│  │  export_to_er1()  |  record_impression()               │  │
│  └──────┬──────────────────┬──────────────────┬───────────┘  │
│         │                  │                  │              │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌───────┴──────────┐  │
│  │  ER1 Client   │  │  Whisper     │  │  YT Transcript   │  │
│  │  (er1_client)│  │  Transcriber │  │  API (existing)   │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────┘  │
│         │                                                    │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌─────────────────────────────┐
│  Local MEMORY Folder │     │  ER1 API                    │
│  /Users/kamir/ER1/   │────▶│  POST /upload_2             │
│  MEMORY-{TIMESTAMP}/ │     │  X-API-KEY authentication   │
└─────────────────────┘     └─────────────────────────────┘
```

---

## Implementation Order

| Phase | Effort | Depends on | Delivers |
|-------|--------|-----------|----------|
| 1. ER1 Client | Small | — | Core upload capability |
| 2. DB Extension | Small | — | Tracking state |
| 3. Service Layer | Medium | 1, 2 | export_to_er1(), er1_export_status() |
| 4. Whisper Integration | Small | — | Voice note transcription |
| 5. Web UI | Medium | 3 | Export buttons, filters, impression recording |
| 6. Menu Bar App | Medium | 1, 3, 4 | Export & impression from menu bar |
| 7. Documentation | Small | 5 | User-facing guides |

Phases 1, 2, and 4 are independent and can be built in parallel.
Phase 3 integrates them. Phases 5 and 6 are the UI layers.

---

## Dependencies (New)

```
openai-whisper    # Voice note transcription
simpleaudio       # Audio playback (optional, menu bar)
```

---

## Open Questions

1. **Whisper hosting:** Run Whisper locally (large model, ~3GB VRAM) or use a remote transcription service? The audio-checklist-checker runs it locally.
2. **Browser recording:** Use the MediaRecorder API for in-browser voice capture, or require file upload? MediaRecorder is simpler for the user but adds frontend complexity.
3. **Post-processing scope:** Should the initial version trigger Gemini post-processing, or just prepare the MEMORY folder for the existing audio-checklist-checker pipeline to pick up?
4. **Bulk export:** Should the timeline support "export all filtered" or only individual/checkbox selection?
5. **ER1 API availability:** Should the system queue exports when ER1 is unreachable, or fail immediately?
