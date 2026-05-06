"""Platform-specific cookie decryption for Chrome/Chromium browsers.

Handles different encryption methods used by Chrome on various platforms.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ._errors import CookieError


try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers import (
        Cipher,
        algorithms,
        modes,
    )

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class ChromeCookieDecryptor:
    """Base class for Chrome cookie decryption."""

    def decrypt(self, encrypted_value: bytes) -> Optional[str]:
        """Decrypt an encrypted cookie value.

        Args:
            encrypted_value: The encrypted cookie bytes

        Returns:
            Decrypted cookie value as string, or None if decryption fails
        """
        raise NotImplementedError


class LinuxChromeCookieDecryptor(ChromeCookieDecryptor):
    """Chrome cookie decryptor for Linux."""

    def __init__(self, browser_root: Path):
        """Initialize Linux decryptor.

        Args:
            browser_root: Path to browser root directory
        """
        if not HAS_CRYPTOGRAPHY:
            raise CookieError(
                "Cookie decryption requires 'cryptography' package. "
                "Install with: pip install 'youtube-transcript-api[cookies]'"
            )

        # v10 uses hardcoded password
        self.v10_key = self._derive_key(b"peanuts")

        # v11 uses keyring password (try to get it, fall back to v10)
        self.v11_key = self._get_v11_key() or self.v10_key

    def _derive_key(self, password: bytes, iterations: int = 1) -> bytes:
        """Derive encryption key using PBKDF2.

        Args:
            password: Password bytes
            iterations: PBKDF2 iterations

        Returns:
            Derived key bytes
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA1(),
            length=16,
            salt=b"saltysalt",
            iterations=iterations,
            backend=default_backend(),
        )
        return kdf.derive(password)

    def _get_v11_key(self) -> Optional[bytes]:
        """Try to get v11 key from keyring.

        Returns:
            Derived key or None if keyring access fails
        """
        # Try to get password from GNOME Keyring or KWallet
        # This is optional - we'll fall back to v10 if it fails
        try:
            # Try secretstorage (GNOME Keyring)
            import secretstorage

            bus = secretstorage.dbus_init()
            collection = secretstorage.get_default_collection(bus)
            for item in collection.get_all_items():
                if item.get_label() == "Chrome Safe Storage":
                    password = item.get_secret()
                    return self._derive_key(password)
        except Exception:
            pass

        return None

    def decrypt(self, encrypted_value: bytes) -> Optional[str]:
        """Decrypt Chrome cookie on Linux.

        Args:
            encrypted_value: Encrypted cookie bytes

        Returns:
            Decrypted value or None
        """
        if not encrypted_value:
            return None

        # Check version
        version = encrypted_value[:3]

        if version == b"v10":
            key = self.v10_key
            encrypted_value = encrypted_value[3:]
        elif version == b"v11":
            key = self.v11_key
            encrypted_value = encrypted_value[3:]
        else:
            # Try as v10 anyway
            key = self.v10_key

        try:
            # Decrypt using AES-CBC
            iv = b" " * 16  # Chrome uses spaces as IV
            cipher = Cipher(
                algorithms.AES(key), modes.CBC(iv), backend=default_backend()
            )
            decryptor = cipher.decryptor()
            decrypted = (
                decryptor.update(encrypted_value) + decryptor.finalize()
            )

            # Remove PKCS7 padding
            padding_length = decrypted[-1]
            decrypted = decrypted[:-padding_length]

            return decrypted.decode("utf-8")
        except Exception:
            return None


class MacChromeCookieDecryptor(ChromeCookieDecryptor):
    """Chrome cookie decryptor for macOS."""

    def __init__(self, browser_root: Path):
        """Initialize macOS decryptor.

        Args:
            browser_root: Path to browser root directory
        """
        if not HAS_CRYPTOGRAPHY:
            raise CookieError(
                "Cookie decryption requires 'cryptography' package. "
                "Install with: pip install 'youtube-transcript-api[cookies]'"
            )

        # Get password from macOS Keychain
        password = self._get_keychain_password()
        if password:
            self.key = self._derive_key(password)
        else:
            raise CookieError(
                "Could not retrieve Chrome password from macOS Keychain"
            )

    def _get_keychain_password(self) -> Optional[bytes]:
        """Get Chrome password from macOS Keychain.

        Returns:
            Password bytes or None
        """
        try:
            result = subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-w",
                    "-a",
                    "Chrome",
                    "-s",
                    "Chrome Safe Storage",
                ],
                capture_output=True,
                text=False,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.rstrip(b"\n")
        except Exception:
            pass

        return None

    def _derive_key(self, password: bytes) -> bytes:
        """Derive encryption key using PBKDF2.

        Args:
            password: Password bytes

        Returns:
            Derived key bytes
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA1(),
            length=16,
            salt=b"saltysalt",
            iterations=1003,  # macOS uses 1003 iterations
            backend=default_backend(),
        )
        return kdf.derive(password)

    def decrypt(self, encrypted_value: bytes) -> Optional[str]:
        """Decrypt Chrome cookie on macOS.

        Args:
            encrypted_value: Encrypted cookie bytes

        Returns:
            Decrypted value or None
        """
        if not encrypted_value:
            return None

        # Remove version prefix if present
        if encrypted_value[:3] == b"v10":
            encrypted_value = encrypted_value[3:]

        try:
            # Decrypt using AES-CBC
            iv = b" " * 16  # Chrome uses spaces as IV
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=default_backend(),
            )
            decryptor = cipher.decryptor()
            decrypted = (
                decryptor.update(encrypted_value) + decryptor.finalize()
            )

            # Remove PKCS7 padding
            padding_length = decrypted[-1]
            decrypted = decrypted[:-padding_length]

            return decrypted.decode("utf-8")
        except Exception:
            return None


class WindowsChromeCookieDecryptor(ChromeCookieDecryptor):
    """Chrome cookie decryptor for Windows."""

    def __init__(self, browser_root: Path):
        """Initialize Windows decryptor.

        Args:
            browser_root: Path to browser root directory
        """
        if not HAS_CRYPTOGRAPHY:
            raise CookieError(
                "Cookie decryption requires 'cryptography' package. "
                "Install with: pip install 'youtube-transcript-api[cookies]'"
            )

        # Get encryption key from Local State file
        self.key = self._get_encryption_key(browser_root)
        if not self.key:
            raise CookieError(
                "Could not retrieve Chrome encryption key from Local State"
            )

    def _get_encryption_key(self, browser_root: Path) -> Optional[bytes]:
        """Get encryption key from Local State file.

        Args:
            browser_root: Path to browser root directory

        Returns:
            Decrypted key bytes or None
        """
        local_state_path = browser_root / "Local State"
        if not local_state_path.exists():
            return None

        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.load(f)

            encrypted_key = base64.b64decode(
                local_state["os_crypt"]["encrypted_key"]
            )

            # Remove DPAPI prefix
            if encrypted_key[:5] == b"DPAPI":
                encrypted_key = encrypted_key[5:]

            # Decrypt using Windows DPAPI
            return self._decrypt_with_dpapi(encrypted_key)
        except Exception:
            return None

    def _decrypt_with_dpapi(self, encrypted_data: bytes) -> Optional[bytes]:
        """Decrypt data using Windows DPAPI.

        Args:
            encrypted_data: Encrypted data bytes

        Returns:
            Decrypted data or None
        """
        try:
            import ctypes
            import ctypes.wintypes

            # Define DPAPI structures
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [
                    ("cbData", ctypes.wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_char)),
                ]

            # Load CryptUnprotectData
            crypt_unprotect_data = ctypes.windll.crypt32.CryptUnprotectData
            crypt_unprotect_data.argtypes = [
                ctypes.POINTER(DATA_BLOB),
                ctypes.POINTER(ctypes.wintypes.LPWSTR),
                ctypes.POINTER(DATA_BLOB),
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.wintypes.DWORD,
                ctypes.POINTER(DATA_BLOB),
            ]
            crypt_unprotect_data.restype = ctypes.wintypes.BOOL

            # Prepare input
            blob_in = DATA_BLOB(
                len(encrypted_data),
                ctypes.cast(encrypted_data, ctypes.POINTER(ctypes.c_char)),
            )
            blob_out = DATA_BLOB()

            # Decrypt
            if crypt_unprotect_data(
                ctypes.byref(blob_in),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(blob_out),
            ):
                result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
                # Free memory
                ctypes.windll.kernel32.LocalFree(blob_out.pbData)
                return result
        except Exception:
            pass

        return None

    def decrypt(self, encrypted_value: bytes) -> Optional[str]:
        """Decrypt Chrome cookie on Windows.

        Args:
            encrypted_value: Encrypted cookie bytes

        Returns:
            Decrypted value or None
        """
        if not encrypted_value:
            return None

        # Check version
        if encrypted_value[:3] != b"v10":
            # Try DPAPI decryption for older versions
            decrypted = self._decrypt_with_dpapi(encrypted_value)
            if decrypted:
                try:
                    return decrypted.decode("utf-8")
                except Exception:
                    pass
            return None

        # v10 uses AES-GCM
        encrypted_value = encrypted_value[3:]

        try:
            # Extract nonce and ciphertext
            nonce = encrypted_value[:12]
            ciphertext = encrypted_value[12:]

            # Decrypt using AES-GCM
            aesgcm = AESGCM(self.key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)

            return decrypted.decode("utf-8")
        except Exception:
            return None


def get_chrome_decryptor(browser_root: Path) -> ChromeCookieDecryptor:
    """Get appropriate Chrome cookie decryptor for current platform.

    Args:
        browser_root: Path to browser root directory

    Returns:
        Platform-specific decryptor instance

    Raises:
        CookieError: If platform not supported or decryptor initialization fails
    """
    if sys.platform == "darwin":
        return MacChromeCookieDecryptor(browser_root)
    elif sys.platform in ("win32", "cygwin"):
        return WindowsChromeCookieDecryptor(browser_root)
    else:  # Linux
        return LinuxChromeCookieDecryptor(browser_root)
