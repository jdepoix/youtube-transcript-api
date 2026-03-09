#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

BRANCH="kamir/yt-tools"
REMOTE="kamir"

echo "==> Pulling latest from ${REMOTE}/${BRANCH} ..."
git fetch "$REMOTE"
git merge "${REMOTE}/${BRANCH}" --ff-only

echo ""
echo "Done. Latest changes pulled."
