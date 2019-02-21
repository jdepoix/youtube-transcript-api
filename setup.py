import setuptools


def _get_file_content(file_name):
    with open(file_name, 'r') as file_handler:
        return file_handler.read()

def get_long_description():
    return _get_file_content('README.md')


setuptools.setup(
    name="youtube_transcript_api",
    version="0.1.2",
    author="Jonas Depoix",
    author_email="jonas.depoix@web.de",
    description="This is an python API which allows you to get the transcripts/subtitles for a given YouTube video. It also works for automatically generated subtitles and it does not require a headless browser, like other selenium based solutions do!",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords="youtube-api subtitles youtube transcripts transcript subtitle youtube-subtitles youtube-transcripts cli",
    url="https://github.com/jdepoix/youtube-transcript-api",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'youtube_transcript_api = youtube_transcript_api.__main__:main',
        ],
    },
)
