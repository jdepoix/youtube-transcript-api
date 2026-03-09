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

from PyObjCTools import AppHelper

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
    from youtube_transcript_api._errors import NoTranscriptFound
    log.info("youtube_transcript_api imported successfully")
except Exception as e:
    log.exception("Failed to import youtube_transcript_api")
    raise

# Language code -> flag emoji mapping
LANG_FLAGS = {
    "af": "\U0001f1ff\U0001f1e6", "sq": "\U0001f1e6\U0001f1f1", "am": "\U0001f1ea\U0001f1f9",
    "ar": "\U0001f1f8\U0001f1e6", "hy": "\U0001f1e6\U0001f1f2", "az": "\U0001f1e6\U0001f1ff",
    "eu": "\U0001f1ea\U0001f1f8", "be": "\U0001f1e7\U0001f1fe", "bn": "\U0001f1e7\U0001f1e9",
    "bs": "\U0001f1e7\U0001f1e6", "bg": "\U0001f1e7\U0001f1ec", "ca": "\U0001f1ea\U0001f1f8",
    "zh": "\U0001f1e8\U0001f1f3", "zh-Hans": "\U0001f1e8\U0001f1f3", "zh-Hant": "\U0001f1f9\U0001f1fc",
    "hr": "\U0001f1ed\U0001f1f7", "cs": "\U0001f1e8\U0001f1ff", "da": "\U0001f1e9\U0001f1f0",
    "nl": "\U0001f1f3\U0001f1f1", "en": "\U0001f1ec\U0001f1e7", "et": "\U0001f1ea\U0001f1ea",
    "fi": "\U0001f1eb\U0001f1ee", "fr": "\U0001f1eb\U0001f1f7", "gl": "\U0001f1ea\U0001f1f8",
    "ka": "\U0001f1ec\U0001f1ea", "de": "\U0001f1e9\U0001f1ea", "el": "\U0001f1ec\U0001f1f7",
    "gu": "\U0001f1ee\U0001f1f3", "ht": "\U0001f1ed\U0001f1f9", "ha": "\U0001f1f3\U0001f1ec",
    "he": "\U0001f1ee\U0001f1f1", "hi": "\U0001f1ee\U0001f1f3", "hu": "\U0001f1ed\U0001f1fa",
    "is": "\U0001f1ee\U0001f1f8", "id": "\U0001f1ee\U0001f1e9", "ga": "\U0001f1ee\U0001f1ea",
    "it": "\U0001f1ee\U0001f1f9", "ja": "\U0001f1ef\U0001f1f5", "kn": "\U0001f1ee\U0001f1f3",
    "kk": "\U0001f1f0\U0001f1ff", "ko": "\U0001f1f0\U0001f1f7", "lv": "\U0001f1f1\U0001f1fb",
    "lt": "\U0001f1f1\U0001f1f9", "mk": "\U0001f1f2\U0001f1f0", "ms": "\U0001f1f2\U0001f1fe",
    "ml": "\U0001f1ee\U0001f1f3", "mt": "\U0001f1f2\U0001f1f9", "mr": "\U0001f1ee\U0001f1f3",
    "mn": "\U0001f1f2\U0001f1f3", "ne": "\U0001f1f3\U0001f1f5", "no": "\U0001f1f3\U0001f1f4",
    "nb": "\U0001f1f3\U0001f1f4", "ps": "\U0001f1e6\U0001f1eb", "fa": "\U0001f1ee\U0001f1f7",
    "pl": "\U0001f1f5\U0001f1f1", "pt": "\U0001f1f5\U0001f1f9", "pa": "\U0001f1ee\U0001f1f3",
    "ro": "\U0001f1f7\U0001f1f4", "ru": "\U0001f1f7\U0001f1fa", "sr": "\U0001f1f7\U0001f1f8",
    "sk": "\U0001f1f8\U0001f1f0", "sl": "\U0001f1f8\U0001f1ee", "so": "\U0001f1f8\U0001f1f4",
    "es": "\U0001f1ea\U0001f1f8", "sw": "\U0001f1f0\U0001f1ea", "sv": "\U0001f1f8\U0001f1ea",
    "ta": "\U0001f1ee\U0001f1f3", "te": "\U0001f1ee\U0001f1f3", "th": "\U0001f1f9\U0001f1ed",
    "tr": "\U0001f1f9\U0001f1f7", "uk": "\U0001f1fa\U0001f1e6", "ur": "\U0001f1f5\U0001f1f0",
    "uz": "\U0001f1fa\U0001f1ff", "vi": "\U0001f1fb\U0001f1f3", "cy": "\U0001f3f4\U000e0067\U000e0062\U000e0077\U000e006c\U000e0073\U000e007f",
}


def get_lang_flag(lang_code):
    """Return flag emoji for a language code, or a globe for unknown."""
    return LANG_FLAGS.get(lang_code, "\U0001f310")

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
TRASH_SOUND = "/System/Library/Components/CoreAudio.component/Contents/SharedSupport/SystemSounds/finder/move to trash.aif"


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
            lang_flag = get_lang_flag(entry.get("language", "en"))
            label = f"{lang_flag} {entry['video_id']} - {entry['snippets']} snip - {entry['date']}"
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
            log.info("Re-copied transcript for %s from history (%d chars)", vid, len(text))
            snippets = text.count("\n") + 1
            AppHelper.callAfter(
                lambda: self._show_clipboard_confirmation(vid, snippets, len(text), " (from history)")
            )
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

    @staticmethod
    def _clear_clipboard():
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        proc.communicate(b"")

    @staticmethod
    def _play_trash_sound():
        if os.path.exists(TRASH_SOUND):
            subprocess.Popen(["afplay", TRASH_SOUND])

    def _show_clipboard_confirmation(self, video_id, snippet_count, char_count, lang_note):
        """Show clipboard feedback dialog. Must be called on main thread."""
        self.title = "\U0001f4cb"
        choice = rumps.alert(
            title="\U0001f4cb Transcript in Clipboard",
            message=(
                f"Video: {video_id}{lang_note}\n"
                f"{snippet_count} snippets, {char_count} chars\n\n"
                f"Close to keep clipboard content,\n"
                f"or trash to clear it."
            ),
            ok="Close",
            cancel="\U0001f5d1 Trash",
        )
        if choice == 0:
            self._clear_clipboard()
            self._play_trash_sound()
            self._set_status(f"Clipboard cleared for {video_id}")
            log.info("User trashed clipboard for %s", video_id)
        else:
            self._set_status(f"Clipboard kept: {video_id} ({snippet_count} snippets)")
            log.info("User kept clipboard for %s", video_id)
        self.title = None

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
            transcript_list = self.api.list(video_id)

            # Try English first, then fall back with user choice
            lang_note = ""
            try:
                chosen = transcript_list.find_transcript(["en"])
                log.info("Found English transcript directly")
            except NoTranscriptFound:
                log.info("No English transcript found, looking for alternatives...")
                # Pick the first available transcript (manually created preferred)
                original = None
                for t in transcript_list:
                    original = t
                    break

                if original is None:
                    raise NoTranscriptFound(video_id, ["en"], transcript_list)

                source_lang = original.language_code
                source_flag = get_lang_flag(source_lang)
                log.info("Found transcript in %s (%s)", original.language, source_lang)

                can_translate_en = (
                    original.is_translatable
                    and "en" in original._translation_languages_dict
                )

                if can_translate_en:
                    # Ask user on main thread (macOS requires UI on main thread)
                    en_flag = get_lang_flag("en")
                    result = [None]
                    event = threading.Event()

                    def _ask():
                        result[0] = rumps.alert(
                            title=f"No English transcript for {video_id}",
                            message=(
                                f"Available: {source_flag} {original.language} ({source_lang})\n"
                                f"Translation available: {en_flag} English\n\n"
                                f"Which version do you want?"
                            ),
                            ok=f"{source_flag} {original.language} (original)",
                            cancel=f"{en_flag} English (translated)",
                        )
                        event.set()

                    AppHelper.callAfter(_ask)
                    event.wait()

                    # rumps.alert: ok button -> 1, cancel button -> 0
                    if result[0] == 1:
                        chosen = original
                        lang_note = f" {source_flag} {original.language} ({source_lang})"
                        log.info("User chose original: %s", source_lang)
                    else:
                        chosen = original.translate("en")
                        lang_note = f" {source_flag} English (translated from {source_lang})"
                        log.info("User chose English translation from %s", source_lang)
                else:
                    # No English translation possible, use original
                    chosen = original
                    lang_note = f" {source_flag} {original.language} ({source_lang})"

            transcript = chosen.fetch()
            lang_code = transcript.language_code
            flag = get_lang_flag(lang_code)
            if not lang_note:
                lang_note = f" {flag} {transcript.language}"
            log.info("Received transcript with %d snippets, lang=%s", len(transcript), lang_code)

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
                "language": lang_code,
                "language_note": lang_note.strip(),
                "text": full_text,
            }
            self.history.append(entry)
            save_history(self.history)
            log.info("Saved to history")

            # Update UI
            self._set_status(f"Done: {video_id} ({snippet_count} snippets, {len(full_text)} chars){lang_note}")
            self._rebuild_history_menu()

            # Show clipboard confirmation dialog on main thread
            AppHelper.callAfter(
                lambda: self._show_clipboard_confirmation(
                    video_id, snippet_count, len(full_text), lang_note,
                )
            )

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
