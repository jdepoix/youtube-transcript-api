#!/usr/bin/env python3
"""
YouTube Transcript Grabber - macOS Menu Bar App

Shows an icon in the menu bar. Click to enter a video ID,
preview the video in a browser, and copy the transcript to clipboard.
"""

import json
import logging
import os
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime

import rumps

# --- Logging setup ---
LOG_DIR = os.path.expanduser("~/Library/Logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "YTTranscript.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr),
    ],
)
log = logging.getLogger("YTTranscript")

# --- Project import ---
sys.path.insert(0, "/Users/kamir/GITHUB.kamir/youtube-transcript-api")
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    log.info("youtube_transcript_api imported successfully")
except Exception as e:
    log.exception("Failed to import youtube_transcript_api")
    raise

# --- History persistence ---
HISTORY_FILE = os.path.expanduser("~/Library/Application Support/YTTranscript/history.json")


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt_icon.png")


class YTTranscriptApp(rumps.App):
    def __init__(self):
        icon = ICON_PATH if os.path.exists(ICON_PATH) else None
        super().__init__(
            "YT",
            title=None if icon else "YT",
            icon=icon,
            quit_button=None,
            template=True,
        )
        log.info("Initializing YTTranscriptApp")

        self.history = load_history()
        self.api = YouTubeTranscriptApi()

        # Build menu
        self._status_item = rumps.MenuItem("Status: idle", callback=None)
        self._history_menu = rumps.MenuItem("History")

        # Build initial history items into the submenu
        for item in self._make_history_items():
            self._history_menu.add(item)

        self.menu = [
            rumps.MenuItem("Fetch Transcript...", callback=self.fetch_transcript),
            None,
            self._status_item,
            None,
            self._history_menu,
            None,
            rumps.MenuItem("Open Log File", callback=self.open_log),
            None,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        log.info("App initialized, history has %d entries", len(self.history))

    def _make_history_items(self):
        """Create history menu items from stored history."""
        if not self.history:
            return [rumps.MenuItem("(empty)", callback=None)]
        items = []
        for entry in reversed(self.history[-20:]):
            label = f"{entry['video_id']} - {entry['snippets']} snip - {entry['date']}"
            item = rumps.MenuItem(label, callback=self._re_copy_from_history)
            item._yt_text = entry.get("text", "")
            item._yt_video_id = entry["video_id"]
            items.append(item)
        return items

    def _rebuild_history_menu(self):
        """Rebuild history submenu (only call after app is running)."""
        self._history_menu.clear()
        for item in self._make_history_items():
            self._history_menu.add(item)

    def _re_copy_from_history(self, sender):
        text = getattr(sender, "_yt_text", "")
        vid = getattr(sender, "_yt_video_id", "?")
        if text:
            self._copy_to_clipboard(text)
            self._set_status(f"Copied from history: {vid}")
            log.info("Re-copied transcript for %s from history (%d chars)", vid, len(text))
        else:
            self._set_status(f"No text stored for {vid}")
            log.warning("History entry for %s has no stored text", vid)

    def _set_status(self, msg):
        log.info("Status: %s", msg)
        self._status_item.title = f"Status: {msg}"

    def _clean_video_id(self, raw_input):
        text = raw_input.strip()
        if "youtube.com" in text or "youtu.be" in text:
            if "v=" in text:
                text = text.split("v=")[1]
            elif "youtu.be/" in text:
                text = text.split("youtu.be/")[1]
        text = text.split("&")[0].split("?")[0]
        log.debug("Cleaned video ID: %r -> %r", raw_input, text)
        return text

    @staticmethod
    def _copy_to_clipboard(text):
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        proc.communicate(text.encode("utf-8"))

    @rumps.clicked("Fetch Transcript...")
    def fetch_transcript(self, _):
        log.info("User clicked Fetch Transcript...")
        response = rumps.Window(
            message="Enter a YouTube video ID or URL:",
            title="YouTube Transcript Grabber",
            default_text="",
            ok="Fetch",
            cancel="Cancel",
            dimensions=(320, 24),
        ).run()

        if not response.clicked:
            log.info("User cancelled the dialog")
            return

        raw_input = response.text.strip()
        if not raw_input:
            log.warning("Empty input from user")
            rumps.alert("No video ID entered.")
            return

        video_id = self._clean_video_id(raw_input)
        log.info("Fetching transcript for video_id=%s", video_id)

        # Open preview in browser
        url = f"https://www.youtube.com/watch?v={video_id}"
        log.info("Opening browser: %s", url)
        webbrowser.open(url)

        # Show progress
        self.title = "..."
        self._set_status(f"Fetching {video_id}...")

        thread = threading.Thread(target=self._do_fetch, args=(video_id,), daemon=True)
        thread.start()

    def _do_fetch(self, video_id):
        log.info("Background fetch started for %s", video_id)
        try:
            self._set_status(f"Connecting to YouTube for {video_id}...")
            transcript = self.api.fetch(video_id, languages=["en"])
            log.info("Received transcript with %d snippets", len(transcript))

            self._set_status(f"Processing {len(transcript)} snippets...")
            full_text = "\n".join(snippet.text for snippet in transcript)
            snippet_count = len(transcript)
            log.info("Full text: %d characters, %d snippets", len(full_text), snippet_count)

            self._set_status("Copying to clipboard...")
            self._copy_to_clipboard(full_text)
            log.info("Copied to clipboard")

            # Save to history
            entry = {
                "video_id": video_id,
                "snippets": snippet_count,
                "chars": len(full_text),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "text": full_text,
            }
            self.history.append(entry)
            save_history(self.history)
            log.info("Saved to history")

            # Update UI
            self.title = None
            self._set_status(f"Done: {video_id} ({snippet_count} snippets, {len(full_text)} chars)")
            self._rebuild_history_menu()

            rumps.notification(
                title="Transcript Ready",
                subtitle=f"Video: {video_id}",
                message=f"{snippet_count} snippets copied to clipboard.",
            )
            log.info("Success notification sent")

        except Exception as e:
            log.exception("Fetch failed for %s", video_id)
            self.title = None
            self._set_status(f"ERROR: {video_id} - {e}")
            rumps.notification(
                title="Transcript Error",
                subtitle=f"Video: {video_id}",
                message=str(e)[:200],
            )

    @rumps.clicked("Open Log File")
    def open_log(self, _):
        log.info("Opening log file: %s", LOG_FILE)
        subprocess.Popen(["open", LOG_FILE])


if __name__ == "__main__":
    log.info("=== YT Transcript Grabber starting ===")
    log.info("Log file: %s", LOG_FILE)
    log.info("History file: %s", HISTORY_FILE)
    YTTranscriptApp().run()
