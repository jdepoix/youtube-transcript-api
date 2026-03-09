#!/usr/bin/env bash
set -euo pipefail

APP_NAME="YT Transcript"

if pkill -f "${APP_NAME}.app" 2>/dev/null; then
  echo "Stopped ${APP_NAME}."
else
  echo "${APP_NAME} is not running."
fi
