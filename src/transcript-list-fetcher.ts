import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { parse, HTMLElement } from 'node-html-parser';
import {
  YouTubeTranscriptApiException,
  CouldNotRetrieveTranscript,
  VideoUnavailable,
  YouTubeRequestFailed,
  NoTranscriptFound,
  TranscriptsDisabled,
  NotTranslatable,
  TranslationLanguageNotAvailable,
  FailedToCreateConsentCookie,
  InvalidVideoId,
  IpBlocked,
  RequestBlocked,
  AgeRestricted,
  VideoUnplayable,
  YouTubeDataUnparsable,
  PoTokenRequired,
} from './errors';
import { TranslationLanguage, FetchedTranscript } from './types';
import { WATCH_URL, INNERTUBE_API_URL, INNERTUBE_CONTEXT } from './constants';
import { Transcript } from './transcript'; // Import the Transcript class

// Equivalent to Python's _PlayabilityStatus enum
enum PlayabilityStatus {
  OK = 'OK',
  ERROR = 'ERROR',
  LOGIN_REQUIRED = 'LOGIN_REQUIRED',
  UNPLAYABLE = 'UNPLAYABLE', // Added based on Python code structure, though not explicitly an enum member there
}

// Equivalent to Python's _PlayabilityFailedReason enum
enum PlayabilityFailedReason {
  BOT_DETECTED = 'Sign in to confirm you’re not a bot',
  AGE_RESTRICTED = 'This video may be inappropriate for some users.',
  VIDEO_UNAVAILABLE = 'This video is unavailable',
  // Other reasons can be added if identified from YouTube's responses
}

export class TranscriptList {
  public readonly videoId: string;
  public readonly manuallyCreatedTranscripts: Readonly<Record<string, Transcript>>;
  public readonly generatedTranscripts: Readonly<Record<string, Transcript>>;
  public readonly translationLanguages: ReadonlyArray<TranslationLanguage>;

  constructor(
    videoId: string,
    manuallyCreatedTranscripts: Record<string, Transcript>,
    generatedTranscripts: Record<string, Transcript>,
    translationLanguages: TranslationLanguage[],
  ) {
    this.videoId = videoId;
    this.manuallyCreatedTranscripts = Object.freeze(manuallyCreatedTranscripts);
    this.generatedTranscripts = Object.freeze(generatedTranscripts);
    this.translationLanguages = Object.freeze(translationLanguages);
  }

  findTranscript(languageCodes: string[]): Transcript {
    return this._findTranscript(languageCodes, [
      this.manuallyCreatedTranscripts,
      this.generatedTranscripts,
    ]);
  }

  findGeneratedTranscript(languageCodes: string[]): Transcript {
    return this._findTranscript(languageCodes, [this.generatedTranscripts]);
  }

  findManuallyCreatedTranscript(languageCodes: string[]): Transcript {
    return this._findTranscript(languageCodes, [this.manuallyCreatedTranscripts]);
  }

  private _findTranscript(
    languageCodes: string[],
    transcriptDicts: Array<Readonly<Record<string, Transcript>>>,
  ): Transcript {
    for (const langCode of languageCodes) {
      for (const transcriptDict of transcriptDicts) {
        if (transcriptDict[langCode]) {
          return transcriptDict[langCode];
        }
      }
    }
    throw new NoTranscriptFound(this.videoId, languageCodes.join(', '), this);
  }

  *[Symbol.iterator](): Iterator<Transcript> {
    for (const langCode in this.manuallyCreatedTranscripts) {
      yield this.manuallyCreatedTranscripts[langCode];
    }
    for (const langCode in this.generatedTranscripts) {
      yield this.generatedTranscripts[langCode];
    }
  }

  toString(): string {
    const मैनुअलीरूप से निर्मित = Object.values(this.manuallyCreatedTranscripts)
      .map(t => `  - ${t.languageCode} ("${t.language}")${t.isTranslatable ? ' [TRANSLATABLE]' : ''}`)
      .join('\n');
    const उत्पन्न = Object.values(this.generatedTranscripts)
      .map(t => `  - ${t.languageCode} ("${t.language}")${t.isTranslatable ? ' [TRANSLATABLE]' : ''}`)
      .join('\n');
    const अनुवाद भाषाएँ = this.translationLanguages
      .map(t => `  - ${t.languageCode} ("${t.language}")`)
      .join('\n');

    return (
      `For this video (${this.videoId}) transcripts are available in the following languages:\n\n` +
      `(MANUALLY CREATED)\n${मैनुअलीरूप से निर्मित || '  None'}\n\n` +
      `(GENERATED)\n${उत्पन्न || '  None'}\n\n` +
      `(TRANSLATION LANGUAGES)\n${अनुवाद भाषाएँ || '  None'}`
    );
  }
}

// Helper to build TranscriptList. In Python, this is a static method of TranscriptList.
// For TypeScript, it can be a standalone function or part of TranscriptListFetcher if it makes sense.
function buildTranscriptList(
  httpClient: AxiosInstance,
  videoId: string,
  captionsJson: any, // Type this more accurately based on expected JSON structure
): TranscriptList {
  const translationLanguages: TranslationLanguage[] = (captionsJson.translationLanguages || []).map((lang: any) => ({
    language: lang.languageName.runs[0].text,
    languageCode: lang.languageCode,
  }));

  const manuallyCreatedTranscripts: Record<string, Transcript> = {};
  const generatedTranscripts: Record<string, Transcript> = {};

  for (const caption of captionsJson.captionTracks) {
    const isGenerated = caption.kind === 'asr';
    const transcriptDict = isGenerated ? generatedTranscripts : manuallyCreatedTranscripts;
    const url = caption.baseUrl.replace('&fmt=srv3', ''); // srv3 is an old format

    // Instantiate the Transcript class
    const transcriptEntry = new Transcript(
      httpClient,
      videoId,
      url,
      caption.name.runs[0].text,
      caption.languageCode,
      isGenerated,
      caption.isTranslatable ? translationLanguages : [],
      // Default preserveFormatting to false, can be made configurable if needed
      false
    );
    transcriptDict[caption.languageCode] = transcriptEntry;
  }

  return new TranscriptList(
    videoId,
    manuallyCreatedTranscripts,
    generatedTranscripts,
    translationLanguages
  );
}

export class TranscriptListFetcher {
  private httpClient: AxiosInstance;
  // private proxyConfig: any; // Define ProxyConfig interface if needed

  constructor(httpClient: AxiosInstance /*, proxyConfig?: any*/) {
    this.httpClient = httpClient;
    // this.proxyConfig = proxyConfig;
  }

  async fetch(videoId: string): Promise<TranscriptList> {
    const captionsJson = await this._fetchCaptionsJson(videoId);
    return buildTranscriptList(this.httpClient, videoId, captionsJson);
  }

  private async _fetchCaptionsJson(videoId: string, tryNumber: number = 0): Promise<any> {
    try {
      const html = await this._fetchVideoHtml(videoId);
      const apiKey = this._extractInnertubeApiKey(html, videoId);
      const innertubeData = await this._fetchInnertubeData(videoId, apiKey);
      return this._extractCaptionsJson(innertubeData, videoId);
    } catch (error) {
      if (error instanceof RequestBlocked /* && this.proxyConfig */) {
        // const retries = this.proxyConfig?.retriesWhenBlocked ?? 0;
        // if (tryNumber + 1 < retries) {
        //   return this._fetchCaptionsJson(videoId, tryNumber + 1);
        // }
        // error.withProxyConfig(this.proxyConfig) // Add this method to RequestBlocked if needed
      }
      throw error;
    }
  }

  private _extractInnertubeApiKey(html: string, videoId: string): string {
    const match = html.match(/"INNERTUBE_API_KEY":\s*"([a-zA-Z0-9_-]+)"/);
    if (match && match[1]) {
      return match[1];
    }
    if (html.includes('class="g-recaptcha"')) {
      throw new IpBlocked(videoId);
    }
    // In Python, this was YouTubeDataUnparsable.
    // It might be more specific if we can determine other failure modes.
    throw new YouTubeDataUnparsable(videoId, "Could not extract INNERTUBE_API_KEY. YouTube's HTML structure may have changed.");
  }

  private _extractCaptionsJson(innertubeData: any, videoId: string): any {
    this._assertPlayability(innertubeData?.playabilityStatus, videoId);

    const captionsJson = innertubeData?.captions?.playerCaptionsTracklistRenderer;
    if (!captionsJson || !captionsJson.captionTracks) {
      throw new TranscriptsDisabled(videoId);
    }
    return captionsJson;
  }

  private _assertPlayability(playabilityStatusData: any, videoId: string): void {
    const status = playabilityStatusData?.status as PlayabilityStatus;

    if (status && status !== PlayabilityStatus.OK) {
      const reason = playabilityStatusData.reason as string | undefined;
      if (status === PlayabilityStatus.LOGIN_REQUIRED) {
        if (reason === PlayabilityFailedReason.BOT_DETECTED) {
          throw new RequestBlocked(videoId); // Or IpBlocked, depending on context
        }
        if (reason === PlayabilityFailedReason.AGE_RESTRICTED) {
          throw new AgeRestricted(videoId);
        }
      }

      if (status === PlayabilityStatus.ERROR && reason === PlayabilityFailedReason.VIDEO_UNAVAILABLE) {
        if (videoId.startsWith('http://') || videoId.startsWith('https://')) {
          throw new InvalidVideoId(videoId);
        }
        throw new VideoUnavailable(videoId);
      }

      // Fallback for other unplayable scenarios
      const subreasonRuns = playabilityStatusData?.errorScreen?.playerErrorMessageRenderer?.subreason?.runs;
      const subreasons: string[] = Array.isArray(subreasonRuns)
        ? subreasonRuns.map((run: any) => run?.text || '').filter(text => text)
        : [];
      throw new VideoUnplayable(videoId, reason, subreasons);
    }
    // If playabilityStatusData is missing but the video is fine, it might not be an issue.
    // However, if it's missing and later calls fail, this might be a point of failure.
    // For now, only throw if status is explicitly not OK.
  }

  private async _createConsentCookie(html: string, videoId: string): Promise<void> {
    // In a browser environment, document.cookie would be used.
    // For Node.js, axios's cookie jar (if configured) or manual cookie management is needed.
    // This simplified version assumes the http client handles cookies.
    const match = html.match(/name="v" value="(.*?)"/);
    if (!match || !match[1]) {
      throw new FailedToCreateConsentCookie(videoId);
    }
    // This is a conceptual representation. Actual cookie setting depends on http client capabilities.
    // e.g., if using axios-cookiejar-support
    // this.httpClient.defaults.jar.setCookie(`CONSENT=YES+${match[1]}`, 'https://www.youtube.com');
    // For now, we'll assume the client is configured to handle cookies or this needs to be handled by the caller.
    console.warn("Cookie consent setting is not fully implemented in this environment. Manual cookie management might be needed for the HTTP client.");
  }

  private async _fetchVideoHtml(videoId: string): Promise<string> {
    let html = await this._fetchHtml(videoId, WATCH_URL.replace('{video_id}', videoId));
    if (html.includes('action="https://consent.youtube.com/s"')) {
      await this._createConsentCookie(html, videoId); // This may set cookies on the httpClient
      html = await this._fetchHtml(videoId, WATCH_URL.replace('{video_id}', videoId)); // Re-fetch with consent
      if (html.includes('action="https://consent.youtube.com/s"')) {
        throw new FailedToCreateConsentCookie(videoId, "Failed to bypass consent page even after attempting to set cookie.");
      }
    }
    return html;
  }

  private async _fetchHtml(videoId: string, url: string): Promise<string> {
    try {
      const response: AxiosResponse<string> = await this.httpClient.get(url, {
        headers: {
          // YouTube might block requests without a common user-agent
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
      });
      // Basic unescape for HTML entities, node-html-parser might handle more complex cases if used for parsing the whole doc
      return response.data.replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new YouTubeRequestFailed(videoId, error);
      }
      throw error; // Re-throw other errors
    }
  }

  private async _fetchInnertubeData(videoId: string, apiKey: string): Promise<any> {
    const url = INNERTUBE_API_URL.replace('{api_key}', apiKey);
    try {
      const response: AxiosResponse<any> = await this.httpClient.post(url, {
        context: INNERTUBE_CONTEXT,
        videoId: videoId,
      }, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        // Inspect error.response.data for specific YouTube error messages if available
        // This could provide more context than just the HTTP error status
        throw new YouTubeRequestFailed(videoId, error);
      }
      throw error;
    }
  }
}

// Example of how TranscriptParser might look (very basic, needs proper implementation)
// class TranscriptParser {
//   private preserveFormatting: boolean;
//   private htmlRegex: RegExp;

//   constructor(preserveFormatting: boolean = false) {
//     this.preserveFormatting = preserveFormatting;
//     // This regex needs to be carefully translated from the Python version
//     // For now, a simple strip-tags regex
//     this.htmlRegex = /<[^>]*>/g;
//   }

//   parse(rawData: string): FetchedTranscriptSnippet[] {
//     // This is where XML parsing or robust string manipulation for transcript data would happen.
//     // The Python version uses ElementTree. For simple XML, regex or a lightweight parser might work.
//     // For now, this is a placeholder.
//     console.warn("TranscriptParser.parse() is not fully implemented.");
//     return [];
//   }
// }

// TODO:
// 1. Refine error handling and type definitions for JSON structures (captionsJson, innertubeData).
// 4. Add proxy configuration if needed.
// 5. Test thoroughly with various YouTube video scenarios.
// 6. Consider unescape for HTML entities more robustly. node-html-parser's parse function
//    might handle this if the entire HTML is parsed, or a dedicated unescape library.
//    The current _fetchHtml has a very basic unescape.
// 7. Cookie handling for _createConsentCookie with axios might require `axios-cookiejar-support`
//    or manual management if not running in a browser. The current implementation has a console warning.
// 8. The `INNERTUBE_CONTEXT.client.clientVersion` might need periodic updates
//    to mimic current browser versions for YouTube.
// 9. `PoTokenRequired` error in Transcript.fetch placeholder: ensure this logic is correctly placed
//    when Transcript class is fully implemented.
// 10. `NoTranscriptFound` error in `findTranscriptLogic` was passing `this` (TranscriptList instance)
//     The error constructor expects videoId, requestedLanguageCodes (string), and transcriptData (any).
//     Adjusted to pass `transcriptList.videoId`, `languageCodes.join(', ')`, and `transcriptList`.
// 11. `YouTubeDataUnparsable` in `_extractInnertubeApiKey` now takes a message.
// 12. `FailedToCreateConsentCookie` in `_fetchVideoHtml` now takes a message.
// 13. `VideoUnplayable` constructor in `_assertPlayability` now matches the error class definition.
// 14. Added User-Agent headers to _fetchHtml and _fetchInnertubeData as YouTube often blocks requests without it.
// 15. `Transcript` interface and `buildTranscriptList`'s `Transcript` object now include `httpClient`
//     as it's used in the Python `Transcript` class for its methods.
// 16. The `Transcript` methods `fetch` and `translate` in the placeholder are async and return Promises.
//     The actual implementation will need to be async.
// 17. `findTranscriptLogic` was added to avoid code duplication in `TranscriptList` implementation.
// 18. `PlayabilityStatus` got an `UNPLAYABLE` member, which seems to be implicitly handled in Python's `_assert_playability`.
//     The TypeScript version makes this more explicit.
// 19. `RequestBlocked` error in `_fetchCaptionsJson` regarding proxy retries is commented out for now
//     as proxy configuration (`this.proxyConfig`) is not yet implemented.
// 20. `NoTranscriptFound` in `findTranscriptLogic` was passing `transcriptList` as `transcriptData`.
//     The Python equivalent also passes the `TranscriptList` instance.
// 21. `InvalidVideoId` in `_assertPlayability` now correctly passes `videoId`.
// 22. `AgeRestricted` in `_assertPlayability` now correctly passes `videoId`.
// 23. `TranscriptsDisabled` in `_extractCaptionsJson` now correctly passes `videoId`.
// 24. `IpBlocked` in `_extractInnertubeApiKey` now correctly passes `videoId`.
// 25. `FailedToCreateConsentCookie` in `_createConsentCookie` now correctly passes `videoId`.
