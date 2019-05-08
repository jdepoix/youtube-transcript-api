# YouTube Transcript/Subtitle API (including automatically generated subtitles)

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=BAENLEW8VUJ6G&source=url)
[![Build Status](https://travis-ci.org/jdepoix/youtube-transcript-api.svg)](https://travis-ci.org/jdepoix/youtube-transcript-api)
[![Coverage Status](https://coveralls.io/repos/github/jdepoix/youtube-transcript-api/badge.svg?branch=master)](https://coveralls.io/github/jdepoix/youtube-transcript-api?branch=master)
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](http://opensource.org/licenses/MIT)
[![image](https://img.shields.io/pypi/v/youtube-transcript-api.svg)](https://pypi.org/project/youtube-transcript-api/)
[![image](https://img.shields.io/pypi/pyversions/youtube-transcript-api.svg)](https://pypi.org/project/youtube-transcript-api/)

This is an python API which allows you to get the transcripts/subtitles for a given YouTube video. It also works for automatically generated subtitles and it does not require a headless browser, like other selenium based solutions do!

## Install

It is recommended to [install this module by using pip](https://pypi.org/project/youtube-transcript-api/):

```
pip install youtube_transcript_api
```

If you want to use it from source, you'll have to install the dependencies manually:

```
pip install -r requirements.txt
```

## How to use it

You could either integrate this module into an existing application, or just use it via an CLI

### In code

To get a transcript for a given video you can do:

```python
from youtube_transcript_api import YouTubeTranscriptApi

YouTubeTranscriptApi.get_transcript(video_id)
```

This will return a list of dictionaries looking somewhat like this:

```python
[
    {
        'text': 'Hey there',
        'start': 7.58,
        'duration': 6.13
    },
    {
        'text': 'how are you',
        'start': 14.08,
        'duration': 7.58
    },
    # ...
]
```

You can also add the `languages` param if you want to make sure the transcripts are retrieved in your desired language (it usually defaults to english).

```python
YouTubeTranscriptApi.get_transcripts(video_ids, languages=['de', 'en'])
```

It's a list of language codes in a descending priority. In this example it will first try to fetch the german transcript (`'de'`) and then fetch the english transcript (`'en'`) if it fails to do so. As I can't provide a complete list of all working language codes with full certainty, you may have to play around with the language codes a bit, to find the one which is working for you!

To get transcripts for a list fo video ids you can call:

```python
YouTubeTranscriptApi.get_transcripts(video_ids, languages=['de', 'en'])
```

`languages` also is optional here.

### CLI

Execute the CLI script using the video ids as parameters and the results will be printed out to the command line:

```
youtube_transcript_api <first_video_id> <second_video_id> ...
```

The CLI also gives you the option to provide a list of preferred languages:

```
youtube_transcript_api <first_video_id> <second_video_id> ... --languages de en
```

If you would prefer to write it into a file or pipe it into another application, you can also output the results as json using the following line:

```
youtube_transcript_api <first_video_id> <second_video_id> ... --languages de en --json > transcripts.json
```

### Proxy

You can specify a https/http proxy, which will be used during the requests to YouTube:

```python
from youtube_transcript_api import YouTubeTranscriptApi

YouTubeTranscriptApi.get_transcript(video_id, proxies={"http": "http://user:pass@domain:port", "https": "https://user:pass@domain:port"})
```

As the `proxies` dict is passed on to the `requests.get(...)` call, it follows the [format used by the requests library](http://docs.python-requests.org/en/master/user/advanced/#proxies).

Using the CLI:

```
youtube_transcript_api <first_video_id> <second_video_id> --http-proxy http://user:pass@domain:port --https-proxy https://user:pass@domain:port
```


## Warning

 This code uses an undocumented part of the YouTube API, which is called by the YouTube web-client. So there is no guarantee that it won't stop working tomorrow, if they change how things work. I will however do my best to make things working again as soon as possible if that happens. So if it stops working, let me know!

## Donation

If this project makes you happy by reducing your development time, you can make me happy by treating me to a cup of coffee :)

[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=BAENLEW8VUJ6G&source=url)