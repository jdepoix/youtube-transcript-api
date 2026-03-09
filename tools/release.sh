#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

VERSION="${1:?Usage: tools/release.sh <version>  (e.g. 1.1.0)}"
TAG="v${VERSION}"
ZIP_NAME="YT-Transcript-${VERSION}-macOS.zip"

echo "==> Building YT Transcript ${VERSION} ..."

# Clean and build
rm -rf build dist
python3 setup_app.py py2app 2>&1 | tail -1

# Zip the .app bundle
echo "==> Packaging ${ZIP_NAME} ..."
cd dist
zip -qr "../${ZIP_NAME}" "YT Transcript.app"
cd ..

echo "==> Built: ${ZIP_NAME} ($(du -h "${ZIP_NAME}" | cut -f1))"
echo ""
echo "To create the GitHub release:"
echo ""
echo "  git tag ${TAG} && git push kamir ${TAG}"
echo "  gh release create ${TAG} ${ZIP_NAME} --title \"YT Transcript ${VERSION}\" --notes \"macOS menu bar app for YouTube transcripts.\""
echo ""
echo "After the release, users install with:"
echo ""
echo "  curl -fsSL https://api.github.com/repos/kamir/youtube-transcript-api/contents/tools/install.sh?ref=kamir/yt-tools -H 'Accept: application/vnd.github.raw' | bash"
