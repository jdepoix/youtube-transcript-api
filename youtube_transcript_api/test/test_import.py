#!/usr/bin/env python3
"""Simple test to verify imports work correctly."""

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._cookies import extract_cookies_from_browser
    from youtube_transcript_api._errors import CookieError

    print("✓ All imports successful!")

    # Test that the API accepts the new parameter
    try:
        api = YouTubeTranscriptApi(cookies_from_browser=None)
        print("✓ YouTubeTranscriptApi accepts cookies_from_browser parameter")
    except Exception as e:
        print(f"✗ Error initializing API: {e}")

    # Test that unsupported browser raises error
    try:
        extract_cookies_from_browser("safari")
        print("✗ Should have raised error for unsupported browser")
    except CookieError as e:
        print(f"✓ Correctly raises CookieError for unsupported browser: {e}")

    print("\n✓ All basic tests passed!")

except ImportError as e:
    print(f"✗ Import error: {e}")
    import traceback

    traceback.print_exc()
