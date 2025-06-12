# YouTube Transcript API (TypeScript)

[![npm version](https://badge.fury.io/js/youtube-transcript-api-ts.svg)](https://badge.fury.io/js/youtube-transcript-api-ts)
<!-- Add other badges like build status, license, etc. once CI/npm publishing is set up -->
<!-- e.g. ![Build Status](https://travis-ci.org/user/repo.svg?branch=master) -->
<!-- e.g. ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) -->

This is a TypeScript version of the popular Python library `youtube-transcript-api`, providing an easy way to fetch transcripts (subtitles) for YouTube videos. It works with both manually created and automatically generated transcripts, and does not require headless browsers or complex authentication schemes.

## Features

-   Fetch video transcripts by video ID.
-   List available transcripts for a video, including language codes and whether they are generated or manual.
-   Support for multiple languages and language fallback.
-   Format transcript data into various formats (JSON, pretty JSON, plain text, SRT, WebVTT).
-   Support for fetching transcripts through HTTP/HTTPS proxies.
-   Command-Line Interface (CLI) for easy usage from the terminal.
-   Typed with TypeScript for better developer experience and safety.
-   Specific error types for robust error handling.

## Installation

To install the library, use npm or yarn:

```bash
npm install youtube-transcript-api-ts
# or
yarn add youtube-transcript-api-ts
```
*(Note: The package name `youtube-transcript-api-ts` is a placeholder. The actual name will be determined upon publishing to npm.)*

## Usage (Library)

### Basic Example: Fetching a Transcript

```typescript
import { YouTubeTranscriptApi } from 'youtube-transcript-api-ts';

async function getTranscript(videoId: string) {
  try {
    const api = new YouTubeTranscriptApi(); // Instance for non-static methods
    const transcript = await api.fetch(videoId);
    // By default, fetches the first available transcript (manual preferred, then generated)
    // The result is an array of FetchedTranscriptSnippet objects
    console.log(`Transcript for ${videoId}:`);
    transcript.snippets.forEach(snippet => {
      console.log(`[${snippet.start.toFixed(2)}s - ${(snippet.start + snippet.duration).toFixed(2)}s]: ${snippet.text}`);
    });
  } catch (error) {
    console.error(`Error fetching transcript for ${videoId}:`, error);
  }
}

getTranscript('dQw4w9WgXcQ'); // Example video ID
```

### Listing Available Transcripts

```typescript
import { YouTubeTranscriptApi, TranscriptList } from 'youtube-transcript-api-ts';

async function listAvailableTranscripts(videoId: string) {
  try {
    const api = new YouTubeTranscriptApi();
    const transcriptList: TranscriptList = await api.list(videoId);

    console.log(`Available transcripts for ${videoId}:`);
    for (const transcript of transcriptList) { // TranscriptList is iterable
      console.log(
        `- Language: ${transcript.language} (${transcript.languageCode})`,
        `- Generated: ${transcript.isGenerated}`,
        `- Translatable to: ${transcript.translationLanguages.map(tl => tl.languageCode).join(', ') || 'None'}`
      );
    }
  } catch (error) {
    console.error(`Error listing transcripts for ${videoId}:`, error);
  }
}

listAvailableTranscripts('oHg5SJYRHA0');
```

### Using Different Languages and Fallbacks

```typescript
import { YouTubeTranscriptApi } from 'youtube-transcript-api-ts';

async function getSpecificTranscript(videoId: string) {
  try {
    const api = new YouTubeTranscriptApi();
    // Try to fetch German, if not available, fall back to English
    const transcript = await api.fetch(videoId, ['de', 'en']);
    console.log(`Fetched transcript in ${transcript.languageCode}:`);
    console.log(transcript.snippets.slice(0, 5));
  } catch (error) {
    console.error(error);
  }
}
getSpecificTranscript('oHg5SJYRHA0');
```

### Translating a Transcript

```typescript
import { YouTubeTranscriptApi } from 'youtube-transcript-api-ts';

async function getTranslatedTranscript(videoId: string) {
  try {
    const api = new YouTubeTranscriptApi();
    const transcriptList = await api.list(videoId);
    const englishTranscript = transcriptList.findTranscript(['en']); // Find an English transcript

    if (englishTranscript && englishTranscript.isTranslatable) {
      const germanTranslationMeta = englishTranscript.translationLanguages.find(t => t.languageCode === 'de');
      if (germanTranslationMeta) {
        const translatedTranscript = englishTranscript.translate('de');
        const fetchedTranslated = await translatedTranscript.fetch(); // Fetches the actual translated content
        console.log('German translation:', fetchedTranslated.snippets.slice(0, 3));
      } else {
        console.log('German translation not available for this English transcript.');
      }
    }
  } catch (error) {
    console.error(error);
  }
}
getTranslatedTranscript('oHg5SJYRHA0');
```

### Using Proxies

```typescript
import { YouTubeTranscriptApi, ProxyConfig } from 'youtube-transcript-api-ts';

async function getTranscriptWithProxy(videoId: string) {
  const proxy: ProxyConfig = {
    host: 'your-proxy-host.com',
    port: 8080,
    // auth: { username: 'user', password: 'password' } // Optional
    // protocol: 'http' // Optional, defaults to http by axios if not specified based on URL
  };

  try {
    const api = new YouTubeTranscriptApi(proxy);
    const transcript = await api.fetch(videoId);
    console.log(transcript.snippets.slice(0, 3));
  } catch (error) {
    console.error(error);
  }
}
// getTranscriptWithProxy('oHg5SJYRHA0');
```

### Using Formatters (Directly)

While the CLI uses formatters to produce string output, you can also use them in your code if needed. The API's `fetch` method returns `FetchedTranscript` which contains an array of `FetchedTranscriptSnippet` objects.

```typescript
import { YouTubeTranscriptApi } from 'youtube-transcript-api-ts';
import { SRTFormatter, FetchedTranscript } from 'youtube-transcript-api-ts';
// Assuming types/classes are exported from the main entry point or specific paths

async function getSRTFormattedTranscript(videoId: string) {
  try {
    const api = new YouTubeTranscriptApi();
    const transcriptData: FetchedTranscript = await api.fetch(videoId, ['en']);

    const formatter = new SRTFormatter();
    const srtOutput = formatter.formatTranscript(transcriptData);
    console.log(srtOutput);
  } catch (error) {
    console.error(error);
  }
}
// getSRTFormattedTranscript('oHg5SJYRHA0');
```

## Usage (CLI)

The library provides a command-line interface (CLI) for easy use. After global installation (or using `npx`), you can use it as follows. (The command `youtube-transcript-ts` is configured in `package.json`'s `bin` field).

To run the CLI from the project root after building: `node dist/cli.js <video_id> [options]`

### Basic Examples:

*   **Fetch transcript (default: English, pretty JSON format):**
    ```bash
    youtube-transcript-ts dQw4w9WgXcQ
    ```

*   **Fetch specific languages (e.g., German then English):**
    ```bash
    youtube-transcript-ts dQw4w9WgXcQ --languages de en
    ```

*   **List available transcripts for a video:**
    ```bash
    youtube-transcript-ts dQw4w9WgXcQ --list-transcripts
    ```

*   **Output in SRT format:**
    ```bash
    youtube-transcript-ts dQw4w9WgXcQ --format srt
    ```

*   **Translate to a specific language (e.g., German) and output as text:**
    ```bash
    youtube-transcript-ts oHg5SJYRHA0 --languages en --translate de --format text
    ```

*   **Save output to a file:**
    ```bash
    youtube-transcript-ts dQw4w9WgXcQ --format srt --output-file transcript.srt
    ```

### Key CLI Options:

*   `video-ids...`: One or more YouTube video IDs.
*   `--list-transcripts`, `-l`: List available transcripts.
*   `--languages <lang...>`, `--lang <lang...>`: Preferred languages in order (e.g., `en de`).
*   `--format <format>`: Output format (e.g., `json`, `pretty`, `text`, `srt`, `webvtt`). Default: `pretty`.
*   `--translate <lang_code>`, `-t <lang_code>`: Language code to translate the transcript to.
*   `--output-file <filepath>`, `-o <filepath>`: File to save the output.
*   `--http-proxy <url>`: HTTP proxy URL (e.g., `http://host:port` or `http://user:pass@host:port`).
*   `--https-proxy <url>`: HTTPS proxy URL. (Note: Axios typically uses one proxy; `http-proxy` might cover HTTPS URLs too).
*   `--exclude-generated`: Exclude automatically generated transcripts.
*   `--exclude-manually-created`: Exclude manually created transcripts.
*   `--help`, `-h`: Show help message.

## API Documentation (Brief)

### Main Class: `YouTubeTranscriptApi`

*   **`constructor(proxyConfig?: ProxyConfig, customHttpClient?: AxiosInstance)`**
    *   Creates a new API client instance.
    *   `proxyConfig` (optional): Configuration for an HTTP/HTTPS proxy.
    *   `customHttpClient` (optional): A custom `axios` instance to use for requests.
*   **`async list(videoId: string): Promise<TranscriptList>`**
    *   Fetches and returns a `TranscriptList` object, which contains all available transcripts (manual and generated) for the given video ID.
*   **`async fetch(videoId: string, languages?: string[], preserveFormatting?: boolean): Promise<FetchedTranscript>`**
    *   Fetches the actual transcript content.
    *   `languages` (optional): An array of language codes to try in order of preference. If not provided, it attempts to fetch a transcript based on general availability (manual first).
    *   `preserveFormatting` (optional, default: `false`): If true, attempts to preserve some HTML formatting tags within the transcript text.

### Key Interfaces/Types (exported from `youtube-transcript-api-ts`):

*   **`FetchedTranscript`**:
    *   `videoId: string`
    *   `language: string` (e.g., "English")
    *   `languageCode: string` (e.g., "en")
    *   `isGenerated: boolean`
    *   `snippets: FetchedTranscriptSnippet[]`
*   **`FetchedTranscriptSnippet`**:
    *   `text: string` (The actual transcript text line)
    *   `start: number` (Start time in seconds)
    *   `duration: number` (Duration in seconds)
*   **`TranscriptList`**: (Returned by `api.list()`)
    *   Contains `manuallyCreatedTranscripts: Readonly<Record<string, Transcript>>`
    *   Contains `generatedTranscripts: Readonly<Record<string, Transcript>>`
    *   Contains `translationLanguages: ReadonlyArray<TranslationLanguage>`
    *   Methods like `findTranscript(langs: string[]): Transcript`, etc.
    *   Is iterable, yielding `Transcript` objects.
*   **`Transcript`**: (Represents metadata of a single available transcript)
    *   Properties like `languageCode`, `isGenerated`, `url`, `translationLanguages`.
    *   `async fetch(preserveFormatting?: boolean): Promise<FetchedTranscript>`: Fetches the actual content.
    *   `translate(targetLanguageCode: string): Transcript`: Returns a new `Transcript` object representing the translation metadata.
*   **`ProxyConfig`**: Interface for proxy configuration.
*   **Formatter Classes**: `JSONFormatter`, `PrettyPrintFormatter`, `TextFormatter`, `SRTFormatter`, `WebVTTFormatter`.
*   **Custom Error Classes**: `YouTubeTranscriptApiException` and its subclasses (e.g., `NoTranscriptFound`, `TranscriptsDisabled`).

*(For more detailed API documentation, consider using [TypeDoc](https://typedoc.org/) to generate HTML documentation from the TypeScript source code and comments.)*

## Error Handling

The library throws specific custom errors for various situations, all inheriting from `YouTubeTranscriptApiException`. This allows for fine-grained error handling:

*   `TranscriptsDisabled`: Subtitles are disabled for the video.
*   `NoTranscriptFound`: No transcript could be found for the requested languages.
*   `VideoUnavailable`: The video is unavailable (e.g., private, deleted).
*   `VideoUnplayable`: The video is unplayable for other reasons.
*   `AgeRestricted`: The video is age-restricted.
*   `RequestBlocked` / `IpBlocked`: Request blocked by YouTube.
*   `YouTubeRequestFailed`: A generic error for failed HTTP requests to YouTube.
*   ... and others found in `src/errors.ts`.

Example:
```typescript
import { YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled } from 'youtube-transcript-api-ts';

async function safeGetTranscript(videoId: string) {
  const api = new YouTubeTranscriptApi();
  try {
    const transcript = await api.fetch(videoId, ['nonExistentLang']);
    // ...
  } catch (error) {
    if (error instanceof NoTranscriptFound) {
      console.error('No transcript found for the specified languages:', error.message);
    } else if (error instanceof TranscriptsDisabled) {
      console.error('Transcripts are disabled for this video:', error.message);
    } else {
      console.error('An unexpected error occurred:', error);
    }
  }
}
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.
(Further details can be added here, e.g., regarding development setup, coding standards, running tests.)

## License

This project is licensed under the MIT License.
<!-- Create a LICENSE file with MIT license text if one doesn't exist -->
