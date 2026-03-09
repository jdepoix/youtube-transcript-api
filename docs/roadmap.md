---
layout: default
title: Roadmap & Ideas
---

# Roadmap & Ideas

This project is designed to grow. Below is the living roadmap — a place to track ideas, capture impulses, and plan next steps.

## Current state (v1.1.0)

- [x] Core transcript fetching library (upstream)
- [x] `do_fetch.py` — quick-fetch script with clipboard copy
- [x] macOS menu bar app with language selection and history
- [x] YT History Inspector — OAuth, sync, timeline, word cloud
- [x] Demo Flask app
- [x] Docker support
- [x] One-liner install script
- [x] GitHub Pages documentation

---

## Next up: ER1 Integration (planned)

Standardize the [audio-checklist-checker pattern](https://github.com/kamir/my-ai-X) for YouTube videos. Full requirements: **[ER1 Integration Requirements](requirements-er1-integration)**.

### Phase 1–3: Core ER1 pipeline
- [ ] **ER1 client module** — create MEMORY folders, upload to ER1 API
- [ ] **DB tracking** — `er1_exports` table, track what's been exported
- [ ] **Service layer** — `export_to_er1()`, `er1_export_status()` in HistoryInspector

### Phase 4: Impression capture
- [ ] **Whisper integration** — transcribe user voice notes about videos
- [ ] **Composite payloads** — bundle video transcript + user commentary into one ER1 entry

### Phase 5–6: UI
- [ ] **Web UI** — "Export to ER1" button, "Record Impression", "Not in ER1" filter
- [ ] **Menu bar app** — export & impression actions after transcript fetch

### Phase 7: Post-processing (future)
- [ ] **Gemini tag-to-prompt pipeline** — reuse audio-checklist-checker's prompt mapping

---

## Near-term ideas

### Transcript tools
- [ ] **Batch fetch** — fetch transcripts for a list of video IDs from a file
- [ ] **Export formats** — save transcripts as Markdown, Obsidian notes, or Logseq pages
- [ ] **Transcript search** — full-text search across all stored transcripts
- [ ] **Summary generation** — use an LLM to summarize transcripts (optional integration)

### History Inspector
- [ ] **Tag & categorize** — tag videos by topic, project, or custom labels
- [ ] **Bookmarks / highlights** — mark specific parts of a transcript
- [ ] **Notes per video** — attach personal notes to watched videos
- [ ] **Analytics dashboard** — watch time by topic, daily/weekly trends
- [ ] **Multi-user support** — separate data per Google account

### Menu bar app
- [ ] **Quick search** — search your transcript history from the menu bar
- [ ] **Keyboard shortcut** — global hotkey to trigger transcript fetch
- [ ] **Auto-detect clipboard** — detect YouTube URLs in clipboard and offer to fetch

### Infrastructure
- [ ] **CI/CD pipeline** — GitHub Actions for testing and release automation
- [ ] **Auto-update** — menu bar app checks for new versions on launch
- [ ] **PyPI package** — publish the history inspector as a standalone package

---

## Impulse capture

A scratchpad for raw ideas and impulses. No commitment, no priority — just capture.

_Use GitHub Issues or edit this page directly to add new impulses._

| Date | Impulse | Status |
|------|---------|--------|
| 2026-03-09 | Create gh-pages documentation site | done |
| 2026-03-09 | ER1 integration — standardize audio-checklist-checker pattern for YT videos | planned |
| 2026-03-09 | Impression capture — speak about a video, bundle both transcripts into ER1 | planned |
| | Integrate with Obsidian for knowledge management | idea |
| | Channel-level transcript aggregation | idea |
| | Diff two transcripts (e.g., re-uploads, edits) | idea |
| | Webhook/notification when a channel posts new content | idea |
| | RSS feed of transcripts for followed channels | idea |
| | Transcript quality scoring (auto-generated vs. manual) | idea |
| | Multi-language word clouds | idea |
| | CLI companion to the menu bar app (pipe-friendly) | idea |
| | Browser extension for one-click transcript fetch | idea |

---

## Contributing ideas

Have an idea? Capture it:

1. **Quick:** [Open a GitHub Issue](https://github.com/kamir/youtube-transcript-api/issues/new?labels=idea&title=Idea:+) with the `idea` label
2. **Detailed:** Fork, edit `docs/roadmap.md`, and open a PR
3. **Discuss:** Start a [GitHub Discussion](https://github.com/kamir/youtube-transcript-api/discussions) in the Ideas category

---

Back: [History Inspector](history-inspector) | [Home](/)
