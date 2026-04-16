<pre>
<h1 align="center">
  ✨ YouTube Transcript API 中文文档 ✨
</h1>

<p align="center">
  <a href="https://github.com/sponsors/jdepoix">
    <img src="https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86" alt="赞助">
  </a>
  <a href="https://www.paypal.com/donate/?hosted_button_id=9W5ZHV22FD63G">
    <img src="https://img.shields.io/badge/Donate-PayPal-green.svg" alt="捐赠">
  </a>
  <a href="https://github.com/jdepoix/youtube-transcript-api/actions">
    <img src="https://github.com/jdepoix/youtube-transcript-api/actions/workflows/ci.yml/badge.svg?branch=master" alt="构建状态">
  </a>
  <a href="https://coveralls.io/github/jdepoix/youtube-transcript-api?branch=master">
    <img src="https://coveralls.io/repos/github/jdepoix/youtube-transcript-api/badge.svg?branch=master" alt="覆盖率">
  </a>
  <a href="http://opensource.org/licenses/MIT">
    <img src="http://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat" alt="MIT许可证">
  </a>
  <a href="https://pypi.org/project/youtube-transcript-api/">
    <img src="https://img.shields.io/pypi/v/youtube-transcript-api.svg" alt="当前版本">
  </a>
  <a href="https://pypi.org/project/youtube-transcript-api/">
    <img src="https://img.shields.io/pypi/pyversions/youtube-transcript-api.svg" alt="支持的Python版本">
  </a>
</p>

<p align="center">
  这是一个Python API，允许您检索给定YouTube视频的转录/字幕。它也适用于自动生成的字幕，支持翻译字幕，并且不需要像其他基于Selenium的解决方案那样的无头浏览器！
</p>

<br />

<p align="center">
 <b>如果您更喜欢使用托管解决方案，可以使用我们任何优秀赞助商的服务：</b>
</p>

<p align="center">
  <a href="http://searchapi.io/youtube?via=ytt-api">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://www.searchapi.io/press/v1/svg/searchapi_logo_white_h.svg">
      <source media="(prefers-color-scheme: light)" srcset="https://www.searchapi.io/press/v1/svg/searchapi_logo_black_h.svg">
      <img alt="SearchAPI" src="https://www.searchapi.io/press/v1/svg/searchapi_logo_black_h.svg" height="40px" style="vertical-align: middle;">
    </picture>
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://supadata.ai/youtube-transcript-api?ref=ytt-api">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://supadata.ai/logo-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="https://supadata.ai/logo-light.svg">
      <img alt="supadata" src="https://supadata.ai/logo-light.svg" height="40px">
    </picture>
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.dumplingai.com/endpoints/get-youtube-transcript?via=ytt-api">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://www.dumplingai.com/logos/logo-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="https://www.dumplingai.com/logos/logo-light.svg">
      <img alt="Dumpling AI" src="https://www.dumplingai.com/logos/logo-light.svg" height="40px" style="vertical-align: middle;">
    </picture>
  </a>
</p>

<br />

<p align="center">
  本项目的维护得益于所有<a href="https://github.com/jdepoix/youtube-transcript-api/graphs/contributors">贡献者</a>和<a href="https://github.com/sponsors/jdepoix">赞助商</a>。如果您想赞助本项目并让您的头像或公司标志显示在上面，<a href="https://github.com/sponsors/jdepoix">点击这里</a>。💖
</p>

## 安装

建议使用[pip安装此模块](https://pypi.org/project/youtube-transcript-api/)：

```
pip install youtube-transcript-api
```

您可以将此模块[集成到现有应用程序中](#api)，或者仅通过[CLI](#cli)使用它。

## API

获取给定视频转录的最简单方法是执行：

```python
from youtube_transcript_api import YouTubeTranscriptApi

ytt_api = YouTubeTranscriptApi()
ytt_api.fetch(video_id)
```

> **注意：** 默认情况下，这将尝试访问视频的英文转录。如果您的视频使用其他语言，或者您希望获取其他语言的转录，请阅读下面的章节。

> **注意：** 传入视频ID，而不是视频URL。对于URL为 `https://www.youtube.com/watch?v=12345` 的视频，ID是 `12345`。

这将返回一个类似这样的 `FetchedTranscript` 对象：

```python
FetchedTranscript(
    snippets=[
        FetchedTranscriptSnippet(
            text="你好",
            start=0.0,
            duration=1.54,
        ),
        FetchedTranscriptSnippet(
            text="你好吗",
            start=1.54,
            duration=4.16,
        ),
        # ...
    ],
    video_id="12345",
    language="English",
    language_code="en",
    is_generated=False,
)
```

此对象实现了 `List` 的大部分接口：

```python
ytt_api = YouTubeTranscriptApi()
fetched_transcript = ytt_api.fetch(video_id)

# 可迭代
for snippet in fetched_transcript:
    print(snippet.text)

# 可索引
last_snippet = fetched_transcript[-1]

# 可获取长度
snippet_count = len(fetched_transcript)
```

如果您更喜欢处理原始转录数据，可以调用 `fetched_transcript.to_raw_data()`，它将返回一个字典列表：

```python
[
    {
        'text': '你好',
        'start': 0.0,
        'duration': 1.54
    },
    {
        'text': '你好吗',
        'start': 1.54
        'duration': 4.16
    },
    # ...
]
```

### 获取不同语言

如果您希望确保以所需语言检索转录，可以添加 `languages` 参数（默认为英语）。

```python
YouTubeTranscriptApi().fetch(video_id, languages=['zh', 'en'])
```

这是一个按优先级降序排列的语言代码列表。在此示例中，它将首先尝试获取中文转录（`'zh'`），如果失败，则获取英文转录（`'en'`）。如果您想首先找出哪些语言可用，[请查看 `list()`](#列出可用转录)。

如果您只需要一种语言，您仍然需要将 `languages` 参数格式化为列表：

```python
YouTubeTranscriptApi().fetch(video_id, languages=['zh'])
```

### 保留格式

如果您想保留HTML格式元素，如 `<i>`（斜体）和 `<b>`（粗体），您还可以添加 `preserve_formatting=True`。

```python
YouTubeTranscriptApi().fetch(video_ids, languages=['zh', 'en'], preserve_formatting=True)
```

### 列出可用转录

如果您想列出给定视频的所有可用转录，可以调用：

```python
ytt_api = YouTubeTranscriptApi()
transcript_list = ytt_api.list(video_id)
```

这将返回一个 `TranscriptList` 对象，它是可迭代的，并提供方法来过滤特定语言和类型的转录列表，例如：

```python
transcript = transcript_list.find_transcript(['zh', 'en'])
```

默认情况下，如果请求的语言同时有手动创建和自动生成的转录，此模块始终选择手动创建的转录。`TranscriptList` 允许您通过搜索特定转录类型来绕过此默认行为：

```python
# 过滤手动创建的转录
transcript = transcript_list.find_manually_created_transcript(['zh', 'en'])

# 或自动生成的转录
transcript = transcript_list.find_generated_transcript(['zh', 'en'])
```

`find_generated_transcript`、`find_manually_created_transcript`、`find_transcript` 方法返回 `Transcript` 对象。它们包含有关转录的元数据：

```python
print(
    transcript.video_id,
    transcript.language,
    transcript.language_code,
    # 是手动创建还是YouTube生成
    transcript.is_generated,
    # 此转录是否可以翻译
    transcript.is_translatable,
    # 转录可以翻译到的语言列表
    transcript.translation_languages,
)
```

并提供允许您获取实际转录数据的方法：

```python
transcript.fetch()
```

这将返回一个 `FetchedTranscript` 对象，就像 `YouTubeTranscriptApi().fetch()` 一样。

### 翻译转录

YouTube有一个允许您自动翻译字幕的功能。此模块也可以访问此功能。为此，`Transcript` 对象提供了一个 `translate()` 方法，它返回一个新的翻译后的 `Transcript` 对象：

```python
transcript = transcript_list.find_transcript(['en'])
translated_transcript = transcript.translate('zh')
print(translated_transcript.fetch())
```

### 示例
```python
from youtube_transcript_api import YouTubeTranscriptApi

ytt_api = YouTubeTranscriptApi()

# 检索可用转录
transcript_list = ytt_api.list('video_id')

# 遍历所有可用转录
for transcript in transcript_list:

    # Transcript对象提供元数据属性
    print(
        transcript.video_id,
        transcript.language,
        transcript.language_code,
        # 是手动创建还是YouTube生成
        transcript.is_generated,
        # 此转录是否可以翻译
        transcript.is_translatable,
        # 转录可以翻译到的语言列表
        transcript.translation_languages,
    )

    # 获取实际转录数据
    print(transcript.fetch())

    # 翻译转录将返回另一个转录对象
    print(transcript.translate('zh').fetch())

# 您也可以直接使用转录列表过滤您寻找的语言
transcript = transcript_list.find_transcript(['zh', 'en'])  

# 或仅过滤手动创建的转录  
transcript = transcript_list.find_manually_created_transcript(['zh', 'en'])  

# 或自动生成的转录  
transcript = transcript_list.find_generated_transcript(['zh', 'en'])
```

## 绕过IP封禁（`RequestBlocked` 或 `IpBlocked` 异常）

不幸的是，YouTube已经开始封禁大多数已知属于云服务提供商（如AWS、Google Cloud Platform、Azure等）的IP，这意味着当您将代码部署到任何云解决方案时，很可能会遇到 `RequestBlocked` 或 `IpBlocked` 异常。如果您进行太多请求，您自托管解决方案的IP也可能发生同样情况。您可以使用代理来绕过这些IP封禁。但是，由于YouTube会在长期使用后封禁静态代理，选择轮换住宅代理是最可靠的选项。

有不同的提供商提供轮换住宅代理，但在测试不同的产品后，我发现 [Webshare](https://www.webshare.io/?referral_code=w0xno53eb50g) 最可靠，因此已将其集成到此模块中，以使设置尽可能简单。

### 使用 [Webshare](https://www.webshare.io/?referral_code=w0xno53eb50g)

创建 [Webshare账户](https://www.webshare.io/?referral_code=w0xno53eb50g) 并购买适合您工作负载的"Residential"代理包后（确保不要购买"Proxy Server"或"Static Residential"！），打开 [Webshare代理设置](https://dashboard.webshare.io/proxy/settings?referral_code=w0xno53eb50g) 以检索您的"代理用户名"和"代理密码"。使用此信息，您可以按如下方式初始化 `YouTubeTranscriptApi`：

```python
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username="<代理用户名>",
        proxy_password="<代理密码>",
    )
)

# ytt_api执行的所有请求现在都将通过Webshare代理
ytt_api.fetch(video_id)
```

使用 `WebshareProxyConfig` 将默认使用轮换住宅代理，无需进一步配置。

您还可以将您将轮换的IP池限制为位于特定国家/地区的IP。通过选择靠近运行代码的机器的位置，您可以减少延迟。此外，这可以用于绕过基于位置的限制。

```python
ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username="<代理用户名>",
        proxy_password="<代理密码>",
        filter_ip_locations=["cn", "us"],
    )
)

# Webshare现在将仅轮换位于中国或美国的IP！
ytt_api.fetch(video_id)
```

您可以[在此处](https://www.webshare.io/features/proxy-locations?referral_code=w0xno53eb50g)找到可用位置的完整列表（以及每个位置有多少IP可用）。

请注意，[此处使用了推荐链接](https://www.webshare.io/?referral_code=w0xno53eb50g)，通过这些链接进行的任何购买都将支持此开源项目（当然，无需额外费用！），非常感谢！💖😊🙏💖

但是，如果您更喜欢使用其他提供商或想实现自己的解决方案，您当然可以使用 `GenericProxyConfig` 类集成您自己的代理解决方案，如下一节所述。

### 使用其他代理解决方案

除了使用 [Webshare](#使用-webshare)，您还可以使用 `GenericProxyConfig` 类设置任何通用的HTTP/HTTPS/SOCKS代理：

```python
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

ytt_api = YouTubeTranscriptApi(
    proxy_config=GenericProxyConfig(
        http_url="http://user:pass@my-custom-proxy.org:port",
        https_url="https://user:pass@my-custom-proxy.org:port",
    )
)

# ytt_api执行的所有请求现在都将使用定义的代理URL进行代理
ytt_api.fetch(video_id)
```

请注意，使用代理并不能保证您不会被封禁，因为YouTube始终可以封禁您代理的IP！因此，如果您想最大化可靠性，您应该始终选择轮换代理地址池的解决方案。

## 覆盖请求默认值

初始化 `YouTubeTranscriptApi` 对象时，它将创建一个 `requests.Session`，用于所有HTTP(S)请求。这允许在检索多个请求时缓存cookie。但是，您可以选择将 `requests.Session` 对象传递给其构造函数，如果您想手动在不同的 `YouTubeTranscriptApi` 实例之间共享cookie，覆盖默认值，设置自定义标头，指定SSL证书等。

```python
from requests import Session

http_client = Session()

# 设置自定义标头
http_client.headers.update({"Accept-Encoding": "gzip, deflate"})

# 设置CA_BUNDLE文件路径
http_client.verify = "/path/to/certfile"

ytt_api = YouTubeTranscriptApi(http_client=http_client)
ytt_api.fetch(video_id)

# 在两个YouTubeTranscriptApi实例之间共享相同的Session
ytt_api_2 = YouTubeTranscriptApi(http_client=http_client)
# 现在与ytt_api共享cookie
ytt_api_2.fetch(video_id)
```

## Cookie认证

某些视频有年龄限制，因此如果没有某种认证，此模块将无法访问这些视频。不幸的是，YouTube API的一些最新更改破坏了当前基于cookie的认证实现，因此此功能目前不可用。

## 使用格式化器
格式化器旨在作为您传递给它的转录的额外处理层。目标是将 `FetchedTranscript` 对象转换为给定"格式"的一致字符串。例如基本文本（`.txt`）或甚至有定义规范的格式，如JSON（`.json`）、WebVTT（`.vtt`）、SRT（`.srt`）、逗号分隔格式（`.csv`）等...

`formatters` 子模块提供了一些基本格式化器，可以按原样使用，或根据您的需求进行扩展：

- JSONFormatter
- PrettyPrintFormatter
- TextFormatter
- WebVTTFormatter
- SRTFormatter

以下是从 `formatters` 模块导入的方法。

```python
# 创建自己的格式化器时要继承的基类。
from youtube_transcript_api.formatters import Formatter

# 一些提供的子类，每个输出不同的字符串格式。
from youtube_transcript_api.formatters import JSONFormatter
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api.formatters import WebVTTFormatter
from youtube_transcript_api.formatters import SRTFormatter
```

### 格式化器示例
假设我们想检索一个转录并将其存储到JSON文件。它看起来像这样：

```python
# your_custom_script.py

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter

ytt_api = YouTubeTranscriptApi()
transcript = ytt_api.fetch(video_id)

formatter = JSONFormatter()

# .format_transcript(transcript) 将转录转换为JSON字符串。
json_formatted = formatter.format_transcript(transcript)

# 现在我们可以将其写入文件。
with open('your_filename.json', 'w', encoding='utf-8') as json_file:
    json_file.write(json_formatted)

# 现在应该有一个新的JSON文件，您可以轻松地将其读回Python。
```

**传递额外关键字参数**

由于JSONFormatter利用 `json.dumps()`，您还可以将关键字参数转发到 `.format_transcript(transcript)`，例如通过转发 `indent=2` 关键字参数使您的文件输出更漂亮。

```python
json_formatted = JSONFormatter().format_transcript(transcript, indent=2)
```

### 自定义格式化器示例
您可以实现自己的格式化器类。只需继承 `Formatter` 基类，并确保实现 `format_transcript(self, transcript: FetchedTranscript, **kwargs) -> str` 和 `format_transcripts(self, transcripts: List[FetchedTranscript], **kwargs) -> str` 方法，这些方法在您的格式化器实例上被调用时应该最终返回一个字符串。

```python
class MyCustomFormatter(Formatter):
    def format_transcript(self, transcript: FetchedTranscript, **kwargs) -> str:
        # 在这里进行您的自定义工作，但返回一个字符串。
        return '您的处理后的输出数据作为字符串。'

    def format_transcripts(self, transcripts: List[FetchedTranscript], **kwargs) -> str:
        # 在这里进行您的自定义工作以格式化转录列表，但返回一个字符串。
        return '您的处理后的输出数据作为字符串。'
```

## CLI

使用视频ID作为参数执行CLI脚本，结果将打印到命令行：

```
youtube_transcript_api <第一个视频ID> <第二个视频ID> ...
```

CLI还为您提供提供首选语言列表的选项：

```
youtube_transcript_api <第一个视频ID> <第二个视频ID> ... --languages zh en
```

您还可以指定是否要排除自动生成或手动创建的字幕：

```
youtube_transcript_api <第一个视频ID> <第二个视频ID> ... --languages zh en --exclude-generated
youtube_transcript_api <第一个视频ID> <第二个视频ID> ... --languages zh en --exclude-manually-created
```

如果您希望将其写入文件或将其管道传输到另一个应用程序，您还可以使用以下行将结果输出为json：

```
youtube_transcript_api <第一个视频ID> <第二个视频ID> ... --languages zh en --format json > transcripts.json
```

使用CLI翻译转录也是可能的：

```
youtube_transcript_api <第一个视频ID> <第二个视频ID> ... --languages en --translate zh
```

如果您不确定给定视频有哪些语言可用，您可以调用以列出所有可用转录：

```
youtube_transcript_api --list-transcripts <第一个视频ID>
```

如果视频的ID以连字符开头，您必须使用 `\` 屏蔽连字符，以防止CLI将其误认为参数名称。例如，要获取ID为 `-abc123` 的视频的转录，请运行：

```
youtube_transcript_api "\-abc123"
```

### 使用CLI绕过IP封禁

如果您遇到 `RequestBlocked` 或 `IpBlocked` 错误，因为YouTube封禁了您的IP，您可以使用住宅代理来解决此问题，如[绕过IP封禁](#绕过ip封禁requestblocked-或-ipblocked-异常)中所述。要通过CLI使用 [Webshare "Residential" 代理](https://www.webshare.io/?referral_code=w0xno53eb50g)，您需要创建 [Webshare账户](https://www.webshare.io/?referral_code=w0xno53eb50g) 并购买适合您工作负载的"Residential"代理包（确保不要购买"Proxy Server"或"Static Residential"！）。然后，您可以使用在 [Webshare代理设置](https://dashboard.webshare.io/proxy/settings?referral_code=w0xno53eb50g) 中找到的"代理用户名"和"代理密码"运行以下命令：

```
youtube_transcript_api <第一个视频ID> <第二个视频ID> --webshare-proxy-username "用户名" --webshare-proxy-password "密码"
```

如果您更喜欢使用其他代理解决方案，您可以使用以下命令设置通用HTTP/HTTPS代理：

```
youtube_transcript_api <第一个视频ID> <第二个视频ID> --http-proxy http://user:pass@domain:port --https-proxy https://user:pass@domain:port
```

### 使用CLI进行Cookie认证

要通过CLI使用cookie进行认证，如 [Cookie认证](#cookie认证) 中所述，请运行：

```
youtube_transcript_api <第一个视频ID> <第二个视频ID> --cookies /path/to/your/cookies.txt
```

## 警告

此代码使用YouTube API的未记录部分，这是由YouTube Web客户端调用的。因此，不能保证它不会在明天停止工作，如果他们改变工作方式的话。但是，如果发生这种情况，我将尽最大努力尽快使事情恢复正常工作。因此，如果它停止工作，请告诉我！

## 贡献

要在本地设置项目，请运行以下命令（需要安装 [poetry](https://python-poetry.org/docs/)）：
```shell
poetry install --with test,dev
```

有 [poe](https://github.com/nat-n/poethepoet?tab=readme-ov-file#quick-start) 任务来运行测试、覆盖率、linter和格式化程序（您需要通过所有这些才能使构建通过）：
```shell
poe test
poe coverage
poe format
poe lint
```

如果您只是想确保您的代码通过所有必要的检查以获得绿色构建，您可以简单地运行：
```shell
poe precommit
```

## 捐赠

如果这个项目通过减少您的开发时间让您感到高兴，您可以通过请我喝杯咖啡让我高兴，或者成为本项目的 [赞助商](https://github.com/sponsors/jdepoix) :)

[![捐赠](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=BAENLEW8VUJ6G&source=url)
</pre>
