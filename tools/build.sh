#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Cleaning previous build ..."
rm -rf build dist

echo "==> Installing dependencies ..."
pip3 install -q rumps pyobjc-framework-Cocoa defusedxml requests py2app 2>&1 | tail -1

echo "==> Building YT Transcript.app ..."
python3 setup_app.py py2app 2>&1 | tail -1

echo ""
echo "Done. App bundle: dist/YT Transcript.app"
