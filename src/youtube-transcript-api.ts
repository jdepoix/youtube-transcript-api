import axios, { AxiosInstance, AxiosProxyConfig as AxiosOriginalProxyConfig } from 'axios';
import { TranscriptListFetcher, TranscriptList } from './transcript-list-fetcher';
import { FetchedTranscript, TranslationLanguage } from './types';
import { Transcript } from './transcript';
import { ProxyConfig } from './proxies'; // Our defined ProxyConfig

// Make our ProxyConfig compatible with Axios's for the properties we define.
// AxiosProxyConfig can also be just a URL string, which we are not supporting with our interface directly.
type InternalAxiosProxyConfig = Pick<AxiosOriginalProxyConfig, 'host' | 'port' | 'auth' | 'protocol'>;


export class YouTubeTranscriptApi {
  private httpClient: AxiosInstance;
  private transcriptListFetcher: TranscriptListFetcher;

  constructor(proxyConfig?: ProxyConfig, customHttpClient?: AxiosInstance) {
    if (customHttpClient) {
      this.httpClient = customHttpClient;
    } else {
      this.httpClient = axios.create();
    }

    // Set default headers
    this.httpClient.defaults.headers.common['Accept-Language'] = 'en-US,en;q=0.9';

    if (proxyConfig) {
      const axiosProxySettings: InternalAxiosProxyConfig = {
        host: proxyConfig.host,
        port: proxyConfig.port,
      };
      if (proxyConfig.auth) {
        axiosProxySettings.auth = proxyConfig.auth;
      }
      if (proxyConfig.protocol) {
        axiosProxySettings.protocol = proxyConfig.protocol;
      }
      this.httpClient.defaults.proxy = axiosProxySettings as AxiosOriginalProxyConfig; // Cast needed as AxiosProxyConfig is wider
    }

    this.transcriptListFetcher = new TranscriptListFetcher(this.httpClient);
  }

  async fetch(
    videoId: string,
    languages?: string[],
    preserveFormatting: boolean = false,
  ): Promise<FetchedTranscript> {
    const transcriptList = await this.transcriptListFetcher.fetch(videoId);

    // If specific languages are requested, try to find one.
    // Otherwise, the Python API seems to pick the first available one (implicitly via find_transcript logic).
    // We'll mimic the Python client's behavior: if languages are provided, use them.
    // If not, the Python client would iterate through manually created, then generated.
    // findTranscript([]) in Python raises NoTranscriptFound if list is empty or no languages match.
    // Let's default to trying to find *any* transcript if languages is undefined or empty.

    let targetLanguages: string[];
    if (languages && languages.length > 0) {
      targetLanguages = languages;
    } else {
      // If no languages specified, construct a list of all available language codes to try.
      // This matches behavior of Python's `TranscriptList.find_transcript([])` if it iterates.
      // Or, more simply, we can get the first available if no preference.
      // The Python API's `get_transcript` without languages tries the original language first.
      // Let's get all available and try them.
      const allAvailableLangCodes = [
        ...Object.keys(transcriptList.manuallyCreatedTranscripts),
        ...Object.keys(transcriptList.generatedTranscripts),
      ];
      if (allAvailableLangCodes.length === 0) {
        // This case should ideally be handled by transcriptList.findTranscript([]) throwing NoTranscriptFound
      }
      targetLanguages = allAvailableLangCodes;
    }

    const transcriptToFetch = transcriptList.findTranscript(targetLanguages);
    return transcriptToFetch.fetch(preserveFormatting);
  }

  async list(videoId: string): Promise<TranscriptList> {
    return this.transcriptListFetcher.fetch(videoId);
  }

  // Deprecated methods

  /**
   * @deprecated Use {@link YouTubeTranscriptApi.list} instead.
   * Lists all available transcripts for a given video.
   * @param videoId The ID of the YouTube video.
   * @returns A Promise resolving to the TranscriptList.
   */
  static async list_transcripts(videoId: string, proxyConfig?: ProxyConfig): Promise<TranscriptList> {
    console.warn("YouTubeTranscriptApi.list_transcripts is deprecated. Use new YouTubeTranscriptApi().list() instead.");
    const api = new YouTubeTranscriptApi(proxyConfig);
    return api.list(videoId);
  }

  /**
   * @deprecated Use {@link YouTubeTranscriptApi.fetch} instead.
   * Fetches a transcript for a given video ID and language codes.
   * @param videoId The ID of the YouTube video.
   * @param languages An array of language codes to try (e.g., ['en', 'es']). Defaults to trying the original language.
   * @param preserveFormatting Whether to preserve HTML formatting in the transcript text. Defaults to false.
   * @param proxyConfig Optional proxy configuration.
   * @returns A Promise resolving to the fetched transcript.
   */
  static async get_transcript(
    videoId: string,
    languages?: string[],
    preserveFormatting: boolean = false,
    proxyConfig?: ProxyConfig,
  ): Promise<FetchedTranscript> {
    console.warn("YouTubeTranscriptApi.get_transcript is deprecated. Use new YouTubeTranscriptApi().fetch() instead.");
    const api = new YouTubeTranscriptApi(proxyConfig);
    return api.fetch(videoId, languages, preserveFormatting);
  }

  /**
   * @deprecated Use {@link YouTubeTranscriptApi.fetch} instead. This method is an alias for get_transcript.
   */
  static async get_transcripts(
    videoId: string,
    languages?: string[],
    preserveFormatting: boolean = false,
    proxyConfig?: ProxyConfig,
  ): Promise<FetchedTranscript> {
    console.warn("YouTubeTranscriptApi.get_transcripts is deprecated. Use new YouTubeTranscriptApi().fetch() instead.");
    // In the Python code, get_transcripts was an alias for get_transcript, but it returned a tuple
    // (list_of_snippets, list_of_Transcripts_that_were_tried).
    // The FetchedTranscript type already contains the snippets.
    // For simplicity in this TS version, we'll make it behave like get_transcript.
    // If closer parity for the tuple return is needed, this would need adjustment.
    const api = new YouTubeTranscriptApi(proxyConfig);
    return api.fetch(videoId, languages, preserveFormatting);
  }
}

// Example Usage (for testing purposes, can be removed or moved to a test file)
// async function main() {
//   const api = new YouTubeTranscriptApi();
//   try {
//     const videoId = 'dQw4w9WgXcQ'; // Example video ID
//     console.log(`Fetching transcript list for video: ${videoId}`);
//     const transcriptList = await api.list(videoId);
//     console.log('Available transcripts:');
//     for (const transcript of transcriptList) {
//       console.log(`- ${transcript.language} (${transcript.languageCode})${transcript.isGenerated ? ' (generated)' : ''}`);
//     }

//     if (transcriptList.manuallyCreatedTranscripts['en'] || transcriptList.generatedTranscripts['en']) {
//       console.log('\nFetching English transcript:');
//       const transcript = await api.fetch(videoId, ['en']);
//       transcript.snippets.slice(0, 5).forEach(snippet => {
//         console.log(`[${snippet.start.toFixed(2)}s - ${(snippet.start + snippet.duration).toFixed(2)}s]: ${snippet.text}`);
//       });
//     }

//     // Test deprecated static method
//     console.log('\nTesting deprecated static method list_transcripts:');
//     const staticList = await YouTubeTranscriptApi.list_transcripts(videoId);
//     console.log(`Static list found ${Object.keys(staticList.manuallyCreatedTranscripts).length + Object.keys(staticList.generatedTranscripts).length} items.`);

//   } catch (error) {
//     if (error instanceof Error) {
//       console.error('Error:', error.message);
//       if (error.cause) console.error('Cause:', error.cause);
//     } else {
//       console.error('An unknown error occurred', error);
//     }
//   }
// }

// main();
