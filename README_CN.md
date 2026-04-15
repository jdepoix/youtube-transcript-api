<pre>
# YouTube Transcript API 中文文档

## 简介

这是一个用于获取YouTube视频字幕/转录文本的Python库。

## 安装

```bash
pip install youtube-transcript-api
```

## 基本用法

```python
from youtube_transcript_api import YouTubeTranscriptApi

# 获取视频字幕（替换VIDEO_ID为实际的YouTube视频ID）
transcript = YouTubeTranscriptApi.get_transcript("VIDEO_ID")

# 打印字幕
for line in transcript:
    print(line['text'])
```

## 获取视频ID

YouTube视频ID是网址中 `v=` 后面的部分：

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
# 视频ID是：dQw4w9WgXcQ
```

## 更多信息

查看英文文档：[README.md](README.md)
</pre>
