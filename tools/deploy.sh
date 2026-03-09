#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

APP_NAME="YT Transcript"
INSTALL_DIR="/Applications"
DIST_APP="dist/${APP_NAME}.app"

if [ ! -d "$DIST_APP" ]; then
  echo "ERROR: ${DIST_APP} not found. Run tools/build.sh first."
  exit 1
fi

# Stop running instance
pkill -f "${APP_NAME}.app" 2>/dev/null && echo "==> Stopped running instance." || true
sleep 1

# Remove old version
if [ -d "${INSTALL_DIR}/${APP_NAME}.app" ]; then
  echo "==> Removing previous version ..."
  rm -rf "${INSTALL_DIR}/${APP_NAME}.app"
fi

echo "==> Installing to ${INSTALL_DIR} ..."
cp -R "$DIST_APP" "${INSTALL_DIR}/"
xattr -dr com.apple.quarantine "${INSTALL_DIR}/${APP_NAME}.app" 2>/dev/null || true

echo "==> Launching ..."
open "${INSTALL_DIR}/${APP_NAME}.app"

echo ""
echo "Done. ${APP_NAME} is running in your menu bar."
