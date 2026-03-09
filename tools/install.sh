#!/usr/bin/env bash
set -euo pipefail

APP_NAME="YT Transcript"
REPO="kamir/youtube-transcript-api"
INSTALL_DIR="/Applications"
TMP_DIR=$(mktemp -d)

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "==> Installing ${APP_NAME}.app ..."

# Get latest release download URL
LATEST_URL=$(curl -sfL "https://api.github.com/repos/${REPO}/releases/latest" \
  | grep '"browser_download_url".*\.zip"' \
  | head -1 \
  | cut -d'"' -f4)

if [ -z "$LATEST_URL" ]; then
  echo "ERROR: Could not find a release asset. Check https://github.com/${REPO}/releases"
  exit 1
fi

echo "==> Downloading from ${LATEST_URL} ..."
curl -fsSL "$LATEST_URL" -o "${TMP_DIR}/app.zip"

echo "==> Extracting ..."
unzip -qo "${TMP_DIR}/app.zip" -d "${TMP_DIR}"

# Remove old version if present
if [ -d "${INSTALL_DIR}/${APP_NAME}.app" ]; then
  echo "==> Removing previous version ..."
  rm -rf "${INSTALL_DIR}/${APP_NAME}.app"
fi

echo "==> Installing to ${INSTALL_DIR} ..."
mv "${TMP_DIR}/${APP_NAME}.app" "${INSTALL_DIR}/"

# Clear quarantine flag so macOS doesn't block it
xattr -dr com.apple.quarantine "${INSTALL_DIR}/${APP_NAME}.app" 2>/dev/null || true

echo "==> Launching ..."
open "${INSTALL_DIR}/${APP_NAME}.app"

echo ""
echo "Done! ${APP_NAME} is now in your menu bar."
