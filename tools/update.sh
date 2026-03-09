#!/usr/bin/env bash
set -euo pipefail

TOOLS_DIR="$(dirname "$0")"

echo "========================================="
echo "  YT Transcript — Pull, Build & Deploy"
echo "========================================="
echo ""

"$TOOLS_DIR/pull.sh"
echo ""
"$TOOLS_DIR/build.sh"
echo ""
"$TOOLS_DIR/deploy.sh"
