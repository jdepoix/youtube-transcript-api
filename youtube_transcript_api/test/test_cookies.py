"""Tests for browser cookie extraction functionality."""

import sqlite3
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from youtube_transcript_api._cookies import (
    extract_cookies_from_browser,
    _find_chrome_cookie_db,
    _find_firefox_cookie_db,
    _extract_chrome_cookies,
    _extract_firefox_cookies,
    _get_platform,
)
from youtube_transcript_api._errors import CookiePathInvalid, CookieError

HAS_CRYPTOGRAPHY = find_spec("cryptography") is not None


class TestGetPlatform:
    """Tests for platform detection."""

    def test_get_platform_darwin(self):
        """Test macOS platform detection."""
        with patch("youtube_transcript_api._cookies.sys.platform", "darwin"):
            assert _get_platform() == "Darwin"

    def test_get_platform_windows(self):
        """Test Windows platform detection."""
        with patch("youtube_transcript_api._cookies.sys.platform", "win32"):
            assert _get_platform() == "Windows"

    def test_get_platform_linux(self):
        """Test Linux platform detection."""
        with patch("youtube_transcript_api._cookies.sys.platform", "linux"):
            assert _get_platform() == "Linux"


class TestFindChromeCookieDB:
    """Tests for Chrome cookie database location."""

    def test_find_chrome_cookie_db_not_found(self):
        """Test error when Chrome directory doesn't exist."""
        with patch(
            "youtube_transcript_api._cookies._get_platform",
            return_value="Linux",
        ):
            with patch.object(Path, "exists", return_value=False):
                with pytest.raises(CookiePathInvalid):
                    _find_chrome_cookie_db("chrome")

    def test_find_chrome_cookie_db_no_cookies(self, tmp_path):
        """Test error when cookie database doesn't exist."""
        # Create a mock browser directory
        browser_dir = tmp_path / "chrome"
        browser_dir.mkdir()

        with patch(
            "youtube_transcript_api._cookies._get_platform",
            return_value="Linux",
        ):
            with patch.dict(
                "youtube_transcript_api._cookies.BROWSER_PATHS",
                {"chrome": {"Linux": browser_dir}},
            ):
                with pytest.raises(CookiePathInvalid):
                    _find_chrome_cookie_db("chrome")

    def test_find_chrome_cookie_db_success(self, tmp_path):
        """Test successful cookie database location."""
        # Create a mock browser structure
        browser_dir = tmp_path / "chrome"
        profile_dir = browser_dir / "Default"
        profile_dir.mkdir(parents=True)
        cookie_db = profile_dir / "Cookies"
        cookie_db.touch()

        with patch(
            "youtube_transcript_api._cookies._get_platform",
            return_value="Linux",
        ):
            with patch.dict(
                "youtube_transcript_api._cookies.BROWSER_PATHS",
                {"chrome": {"Linux": browser_dir}},
            ):
                result = _find_chrome_cookie_db("chrome")
                assert result == cookie_db


class TestFindFirefoxCookieDB:
    """Tests for Firefox cookie database location."""

    def test_find_firefox_cookie_db_not_found(self):
        """Test error when Firefox directory doesn't exist."""
        with patch(
            "youtube_transcript_api._cookies._get_platform",
            return_value="Linux",
        ):
            with patch.object(Path, "exists", return_value=False):
                with pytest.raises(CookiePathInvalid):
                    _find_firefox_cookie_db()

    def test_find_firefox_cookie_db_no_profile(self, tmp_path):
        """Test error when no Firefox profile found."""
        firefox_dir = tmp_path / "firefox"
        firefox_dir.mkdir()

        with patch(
            "youtube_transcript_api._cookies._get_platform",
            return_value="Linux",
        ):
            with patch.dict(
                "youtube_transcript_api._cookies.BROWSER_PATHS",
                {"firefox": {"Linux": firefox_dir}},
            ):
                with pytest.raises(CookiePathInvalid):
                    _find_firefox_cookie_db()

    def test_find_firefox_cookie_db_success(self, tmp_path):
        """Test successful Firefox cookie database location."""
        firefox_dir = tmp_path / "firefox"
        profile_dir = firefox_dir / "abc123.default"
        profile_dir.mkdir(parents=True)
        cookie_db = profile_dir / "cookies.sqlite"
        cookie_db.touch()

        with patch(
            "youtube_transcript_api._cookies._get_platform",
            return_value="Linux",
        ):
            with patch.dict(
                "youtube_transcript_api._cookies.BROWSER_PATHS",
                {"firefox": {"Linux": firefox_dir}},
            ):
                result = _find_firefox_cookie_db()
                assert result == cookie_db


class TestExtractFirefoxCookies:
    """Tests for Firefox cookie extraction."""

    def test_extract_firefox_cookies_success(self, tmp_path):
        """Test successful cookie extraction from Firefox."""
        # Create a temporary SQLite database
        cookie_db = tmp_path / "cookies.sqlite"

        conn = sqlite3.connect(cookie_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE moz_cookies (
                name TEXT,
                value TEXT,
                host TEXT
            )
        """)
        cursor.execute(
            "INSERT INTO moz_cookies (name, value, host) VALUES (?, ?, ?)",
            ("CONSENT", "YES+1", ".youtube.com"),
        )
        cursor.execute(
            "INSERT INTO moz_cookies (name, value, host) VALUES (?, ?, ?)",
            ("SESSION_TOKEN", "abc123", ".youtube.com"),
        )
        conn.commit()
        conn.close()

        cookies = _extract_firefox_cookies(cookie_db)

        assert "CONSENT" in cookies
        assert cookies["CONSENT"] == "YES+1"
        assert "SESSION_TOKEN" in cookies
        assert cookies["SESSION_TOKEN"] == "abc123"

    def test_extract_firefox_cookies_empty_db(self, tmp_path):
        """Test extraction from empty database."""
        cookie_db = tmp_path / "cookies.sqlite"

        conn = sqlite3.connect(cookie_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE moz_cookies (
                name TEXT,
                value TEXT,
                host TEXT
            )
        """)
        conn.commit()
        conn.close()

        cookies = _extract_firefox_cookies(cookie_db)
        assert cookies == {}


class TestExtractChromeCookies:
    """Tests for Chrome cookie extraction."""

    def test_extract_chrome_cookies_no_cryptography(self, tmp_path):
        """Test error when cryptography package not installed."""
        cookie_db = tmp_path / "Cookies"
        cookie_db.touch()

        # Mock the import to raise ImportError
        with patch.dict(
            "sys.modules", {"youtube_transcript_api._decryptors": None}
        ):
            # Force reimport to trigger ImportError

            with pytest.raises(CookieError, match="cryptography"):
                _extract_chrome_cookies(cookie_db)

    @pytest.mark.skipif(
        not HAS_CRYPTOGRAPHY,
        reason="cryptography not installed",
    )
    def test_extract_chrome_cookies_success(self, tmp_path):
        """Test successful cookie extraction from Chrome."""
        # Create a temporary SQLite database
        cookie_db = tmp_path / "Cookies"

        conn = sqlite3.connect(cookie_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE cookies (
                name TEXT,
                encrypted_value BLOB,
                value TEXT,
                host_key TEXT
            )
        """)
        # Insert plain text cookie (no encryption)
        cursor.execute(
            "INSERT INTO cookies (name, encrypted_value, value, host_key) VALUES (?, ?, ?, ?)",
            ("CONSENT", b"", "YES+1", ".youtube.com"),
        )
        conn.commit()
        conn.close()

        # Mock the decryptor
        mock_decryptor = Mock()
        mock_decryptor.decrypt = Mock(return_value="decrypted_value")

        with patch(
            "youtube_transcript_api._decryptors.get_chrome_decryptor",
            return_value=mock_decryptor,
        ):
            cookies = _extract_chrome_cookies(cookie_db)

            assert "CONSENT" in cookies
            assert cookies["CONSENT"] == "YES+1"


class TestExtractCookiesFromBrowser:
    """Integration tests for extract_cookies_from_browser."""

    def test_unsupported_browser(self):
        """Test error for unsupported browser."""
        with pytest.raises(CookieError, match="Unsupported browser"):
            extract_cookies_from_browser("safari")

    def test_firefox_integration(self, tmp_path):
        """Test Firefox cookie extraction integration."""
        # Create Firefox structure
        firefox_dir = tmp_path / "firefox"
        profile_dir = firefox_dir / "test.default"
        profile_dir.mkdir(parents=True)
        cookie_db = profile_dir / "cookies.sqlite"

        # Create database
        conn = sqlite3.connect(cookie_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE moz_cookies (
                name TEXT,
                value TEXT,
                host TEXT
            )
        """)
        cursor.execute(
            "INSERT INTO moz_cookies (name, value, host) VALUES (?, ?, ?)",
            ("TEST_COOKIE", "test_value", ".youtube.com"),
        )
        conn.commit()
        conn.close()

        with patch(
            "youtube_transcript_api._cookies._get_platform",
            return_value="Linux",
        ):
            with patch.dict(
                "youtube_transcript_api._cookies.BROWSER_PATHS",
                {"firefox": {"Linux": firefox_dir}},
            ):
                cookies = extract_cookies_from_browser("firefox")

                assert "TEST_COOKIE" in cookies
                assert cookies["TEST_COOKIE"] == "test_value"

    def test_chrome_integration(self, tmp_path):
        """Test Chrome cookie extraction integration."""
        # Create Chrome structure
        chrome_dir = tmp_path / "chrome"
        profile_dir = chrome_dir / "Default"
        profile_dir.mkdir(parents=True)
        cookie_db = profile_dir / "Cookies"

        # Create database
        conn = sqlite3.connect(cookie_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE cookies (
                name TEXT,
                encrypted_value BLOB,
                value TEXT,
                host_key TEXT
            )
        """)
        cursor.execute(
            "INSERT INTO cookies (name, encrypted_value, value, host_key) VALUES (?, ?, ?, ?)",
            ("TEST_COOKIE", b"", "test_value", ".youtube.com"),
        )
        conn.commit()
        conn.close()

        # Mock decryptor
        mock_decryptor = Mock()
        mock_decryptor.decrypt = Mock(return_value=None)

        with patch(
            "youtube_transcript_api._cookies._get_platform",
            return_value="Linux",
        ):
            with patch.dict(
                "youtube_transcript_api._cookies.BROWSER_PATHS",
                {"chrome": {"Linux": chrome_dir}},
            ):
                with patch(
                    "youtube_transcript_api._decryptors.get_chrome_decryptor",
                    return_value=mock_decryptor,
                ):
                    cookies = extract_cookies_from_browser("chrome")

                    # Plain value should be extracted
                    assert "TEST_COOKIE" in cookies
                    assert cookies["TEST_COOKIE"] == "test_value"
