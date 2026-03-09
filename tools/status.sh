#!/usr/bin/env bash

APP_NAME="YT Transcript"
INSTALL_DIR="/Applications"

echo "=== ${APP_NAME} Status ==="
echo ""

# Installed?
if [ -d "${INSTALL_DIR}/${APP_NAME}.app" ]; then
  VERSION=$(defaults read "${INSTALL_DIR}/${APP_NAME}.app/Contents/Info" CFBundleVersion 2>/dev/null || echo "unknown")
  echo "Installed:  yes (${INSTALL_DIR}, v${VERSION})"
else
  echo "Installed:  no"
fi

# Running?
if pgrep -f "${APP_NAME}.app" >/dev/null 2>&1; then
  PID=$(pgrep -f "${APP_NAME}.app" | head -1)
  echo "Running:    yes (PID ${PID})"
else
  echo "Running:    no"
fi

# Build available?
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -d "${SCRIPT_DIR}/dist/${APP_NAME}.app" ]; then
  echo "Build:      dist/${APP_NAME}.app exists"
else
  echo "Build:      no build found"
fi

# Log file
LOG="$HOME/Library/Logs/YTTranscript.log"
if [ -f "$LOG" ]; then
  LINES=$(wc -l < "$LOG" | tr -d ' ')
  SIZE=$(du -h "$LOG" | cut -f1 | tr -d ' ')
  echo "Log:        ${LOG} (${LINES} lines, ${SIZE})"
else
  echo "Log:        none"
fi

# History
HISTORY="$HOME/Library/Application Support/YTTranscript/history.json"
if [ -f "$HISTORY" ]; then
  COUNT=$(python3 -c "import json; print(len(json.load(open('$HISTORY'))))" 2>/dev/null || echo "?")
  echo "History:    ${COUNT} entries"
else
  echo "History:    none"
fi
