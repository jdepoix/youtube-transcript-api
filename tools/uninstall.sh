#!/usr/bin/env bash
set -euo pipefail

APP_NAME="YT Transcript"
INSTALL_DIR="/Applications"

pkill -f "${APP_NAME}.app" 2>/dev/null || true

if [ -d "${INSTALL_DIR}/${APP_NAME}.app" ]; then
  rm -rf "${INSTALL_DIR}/${APP_NAME}.app"
  echo "Removed ${APP_NAME}.app from ${INSTALL_DIR}."
else
  echo "${APP_NAME}.app not found in ${INSTALL_DIR}."
fi

if [ -d "$HOME/Library/Application Support/YTTranscript" ]; then
  rm -rf "$HOME/Library/Application Support/YTTranscript"
  echo "Removed app data."
fi

if [ -f "$HOME/Library/Logs/YTTranscript.log" ]; then
  rm -f "$HOME/Library/Logs/YTTranscript.log"
  echo "Removed log file."
fi

echo "Done. ${APP_NAME} uninstalled."
