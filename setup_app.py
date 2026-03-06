"""
py2app setup for YouTube Transcript Grabber menu bar app.

Usage:
    python3 setup_app.py py2app
"""

from setuptools import setup

APP = ["yt_menubar.py"]
DATA_FILES = [("", ["yt_icon.png"])]
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "YT Transcript",
        "CFBundleDisplayName": "YT Transcript Grabber",
        "CFBundleIdentifier": "com.kamir.yttranscript",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0",
        "LSUIElement": True,  # menu bar app, no dock icon
    },
    "packages": [
        "youtube_transcript_api",
        "requests",
        "defusedxml",
        "rumps",
        "certifi",
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
