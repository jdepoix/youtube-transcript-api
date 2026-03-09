#!/usr/bin/env bash
set -euo pipefail

APP_NAME="YT Transcript"
INSTALL_DIR="/Applications"

if [ ! -d "${INSTALL_DIR}/${APP_NAME}.app" ]; then
  echo "ERROR: ${APP_NAME}.app not found in ${INSTALL_DIR}."
  echo "Run tools/deploy.sh or tools/update.sh first."
  exit 1
fi

if pgrep -f "${APP_NAME}.app" >/dev/null 2>&1; then
  echo "${APP_NAME} is already running."
else
  open "${INSTALL_DIR}/${APP_NAME}.app"
  echo "${APP_NAME} started."
fi
