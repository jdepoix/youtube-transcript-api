"""Browser cookie extraction module.

This module provides functionality to extract cookies directly from browsers
to enable authentication for age-restricted YouTube videos.

Based on yt-dlp's cookie extraction approach.
"""

from __future__ import annotations

import glob
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Optional

from ._errors import CookiePathInvalid, CookieError


# Browser cookie database paths
BROWSER_PATHS = {
    "chrome": {
        "Linux": Path.home() / ".config/google-chrome",
        "Darwin": Path.home() / "Library/Application Support/Google/Chrome",
        "Windows": Path(os.environ.get("LOCALAPPDATA", ""))
        / "Google/Chrome/User Data",
    },
    "chromium": {
        "Linux": Path.home() / ".config/chromium",
        "Darwin": Path.home() / "Library/Application Support/Chromium",
        "Windows": Path(os.environ.get("LOCALAPPDATA", ""))
        / "Chromium/User Data",
    },
    "edge": {
        "Linux": Path.home() / ".config/microsoft-edge",
        "Darwin": Path.home() / "Library/Application Support/Microsoft Edge",
        "Windows": Path(os.environ.get("LOCALAPPDATA", ""))
        / "Microsoft/Edge/User Data",
    },
    "brave": {
        "Linux": Path.home() / ".config/BraveSoftware/Brave-Browser",
        "Darwin": Path.home()
        / "Library/Application Support/BraveSoftware/Brave-Browser",
        "Windows": Path(os.environ.get("LOCALAPPDATA", ""))
        / "BraveSoftware/Brave-Browser/User Data",
    },
    "opera": {
        "Linux": Path.home() / ".config/opera",
        "Darwin": Path.home()
        / "Library/Application Support/com.operasoftware.Opera",
        "Windows": Path(os.environ.get("APPDATA", ""))
        / "Opera Software/Opera Stable",
    },
    "vivaldi": {
        "Linux": Path.home() / ".config/vivaldi",
        "Darwin": Path.home() / "Library/Application Support/Vivaldi",
        "Windows": Path(os.environ.get("LOCALAPPDATA", ""))
        / "Vivaldi/User Data",
    },
    "firefox": {
        "Linux": Path.home() / ".mozilla/firefox",
        "Darwin": Path.home() / "Library/Application Support/Firefox/Profiles",
        "Windows": Path(os.environ.get("APPDATA", ""))
        / "Mozilla/Firefox/Profiles",
    },
}

# Chromium-based browsers
CHROMIUM_BROWSERS = ["chrome", "chromium", "edge", "brave", "opera", "vivaldi"]


def _get_platform() -> str:
    """Get the current platform identifier.

    Returns:
        'Linux', 'Darwin' (macOS), or 'Windows'
    """
    if sys.platform == "darwin":
        return "Darwin"
    elif sys.platform in ("win32", "cygwin"):
        return "Windows"
    else:
        return "Linux"


def _find_chrome_cookie_db(
    browser: str, profile: Optional[str] = None
) -> Path:
    """Find Chrome/Chromium cookie database.

    Args:
        browser: Browser name ('chrome', 'edge', 'brave', etc.)
        profile: Profile name/path (defaults to 'Default')

    Returns:
        Path to cookie database

    Raises:
        CookiePathInvalid: If cookie database not found
    """
    platform = _get_platform()
    base_path = BROWSER_PATHS[browser].get(platform)

    if not base_path or not base_path.exists():
        raise CookiePathInvalid(
            f"{browser} browser directory not found at {base_path}"
        )

    # Default profile
    if profile is None:
        profile = "Default"

    # Check for cookie database in profile directory
    if platform == "Windows":
        # Windows uses 'Network/Cookies' subdirectory
        cookie_db = base_path / profile / "Network" / "Cookies"
    else:
        # Linux/macOS use 'Cookies' directly in profile
        cookie_db = base_path / profile / "Cookies"

    if not cookie_db.exists():
        raise CookiePathInvalid(f"Cookie database not found at {cookie_db}")

    return cookie_db


def _find_firefox_cookie_db(profile: Optional[str] = None) -> Path:
    """Find Firefox cookie database.

    Args:
        profile: Profile directory pattern (optional)

    Returns:
        Path to cookie database

    Raises:
        CookiePathInvalid: If cookie database not found
    """
    platform = _get_platform()
    base_path = BROWSER_PATHS["firefox"].get(platform)

    if not base_path or not base_path.exists():
        raise CookiePathInvalid(
            f"Firefox profile directory not found at {base_path}"
        )

    # Find profile directories
    if profile:
        profile_dirs = glob.glob(str(base_path / f"*{profile}*"))
    else:
        # Look for default profile
        profile_dirs = glob.glob(str(base_path / "*.default*"))

    if not profile_dirs:
        raise CookiePathInvalid(f"No Firefox profile found in {base_path}")

    # Use first matching profile
    profile_dir = Path(profile_dirs[0])
    cookie_db = profile_dir / "cookies.sqlite"

    if not cookie_db.exists():
        raise CookiePathInvalid(f"Cookie database not found at {cookie_db}")

    return cookie_db


def _extract_chrome_cookies(
    cookie_db: Path, domain_filter: str = ".youtube.com"
) -> dict[str, str]:
    """Extract cookies from Chrome cookie database.

    Args:
        cookie_db: Path to cookie database
        domain_filter: Domain to filter cookies (e.g., '.youtube.com')

    Returns:
        Dict of cookie name -> value
    """
    # Import decryptor here to avoid import errors if cryptography not installed
    try:
        from ._decryptors import get_chrome_decryptor
    except ImportError:
        raise CookieError(
            "Cookie decryption requires the 'cryptography' package. "
            "Install it with: pip install 'youtube-transcript-api[cookies]'"
        )

    cookies = {}

    # Copy database to temp directory (in case it's locked)
    with tempfile.TemporaryDirectory() as tmpdir:
        db_copy = Path(tmpdir) / "cookies.db"
        shutil.copy2(cookie_db, db_copy)

        try:
            conn = sqlite3.connect(f"file:{db_copy}?mode=ro", uri=True)
            cursor = conn.cursor()

            # Query cookies for the domain
            cursor.execute(
                "SELECT name, encrypted_value, value, host_key FROM cookies WHERE host_key LIKE ?",
                (f"%{domain_filter}",),
            )

            # Get decryptor
            decryptor = get_chrome_decryptor(cookie_db.parent.parent)

            for (
                name,
                encrypted_value,
                plain_value,
                host_key,
            ) in cursor.fetchall():
                if encrypted_value:
                    try:
                        value = decryptor.decrypt(encrypted_value)
                        if value:
                            cookies[name] = value
                    except Exception:
                        # If decryption fails, skip this cookie
                        pass
                elif plain_value:
                    cookies[name] = plain_value

            conn.close()

        except sqlite3.Error as e:
            raise CookieError(f"Failed to read cookie database: {e}")

    return cookies


def _extract_firefox_cookies(
    cookie_db: Path, domain_filter: str = ".youtube.com"
) -> dict[str, str]:
    """Extract cookies from Firefox cookie database.

    Args:
        cookie_db: Path to cookie database
        domain_filter: Domain to filter cookies

    Returns:
        Dict of cookie name -> value
    """
    cookies = {}

    # Copy database to temp directory (in case it's locked)
    with tempfile.TemporaryDirectory() as tmpdir:
        db_copy = Path(tmpdir) / "cookies.db"
        shutil.copy2(cookie_db, db_copy)

        try:
            conn = sqlite3.connect(f"file:{db_copy}?mode=ro", uri=True)
            cursor = conn.cursor()

            # Query cookies for the domain
            cursor.execute(
                "SELECT name, value FROM moz_cookies WHERE host LIKE ?",
                (f"%{domain_filter}",),
            )

            for name, value in cursor.fetchall():
                if value:
                    cookies[name] = value

            conn.close()

        except sqlite3.Error as e:
            raise CookieError(f"Failed to read Firefox cookie database: {e}")

    return cookies


def extract_cookies_from_browser(
    browser: str,
    profile: Optional[str] = None,
    domain_filter: str = ".youtube.com",
) -> dict[str, str]:
    """Extract cookies from a browser.

    Args:
        browser: Browser name ('chrome', 'firefox', 'edge', 'brave', etc.)
        profile: Profile name/path (optional, defaults to 'Default' for Chrome-based)
        domain_filter: Domain to filter cookies (default: '.youtube.com')

    Returns:
        Dict of cookie name -> value for the specified domain

    Raises:
        CookiePathInvalid: If browser or cookie database not found
        CookieError: If cookie extraction fails

    Example:
        >>> cookies = extract_cookies_from_browser('chrome')
        >>> print(cookies.get('CONSENT'))
    """
    browser = browser.lower()

    if browser not in BROWSER_PATHS:
        raise CookieError(
            f"Unsupported browser: {browser}. "
            f"Supported browsers: {', '.join(BROWSER_PATHS.keys())}"
        )

    if browser == "firefox":
        cookie_db = _find_firefox_cookie_db(profile)
        return _extract_firefox_cookies(cookie_db, domain_filter)
    elif browser in CHROMIUM_BROWSERS:
        cookie_db = _find_chrome_cookie_db(browser, profile)
        return _extract_chrome_cookies(cookie_db, domain_filter)
    else:
        raise CookieError(f"Cookie extraction not implemented for {browser}")
