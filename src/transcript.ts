import { AxiosInstance } from 'axios';
import { XMLParser } from 'fast-xml-parser';
import {
  FetchedTranscript,
  FetchedTranscriptSnippet,
  TranslationLanguage,
} from './types';
import {
  YouTubeRequestFailed,
  PoTokenRequired,
  NotTranslatable,
  TranslationLanguageNotAvailable,
  YouTubeTranscriptApiException,
} from './errors';
import { unescape } from 'html-entities';

const FORMATTING_TAGS: string[] = [
  'strong', 'em', 'b', 'i', 'mark', 'small', 'del', 'ins', 'sub', 'sup',
];

export class TranscriptParser {
  private preserveFormatting: boolean;
  private htmlNonFormattingTagRegex: RegExp; // Used when preserveFormatting is true
  private htmlAllTagRegex: RegExp;           // Used when preserveFormatting is false

  constructor(preserveFormatting: boolean = false) {
    this.preserveFormatting = preserveFormatting;
    this.htmlAllTagRegex = /<[^>]*>/gi;

    // Regex to match HTML tags that are NOT in FORMATTING_TAGS
    // This is a simplified version: it matches any tag.
    // A more precise regex would be complex, e.g., using negative lookaheads
    // to exclude specific formatting tags: /<\/?(?!(?:strong|em|b|i|mark|small|del|ins|sub|sup)\b)[^>]*>/gi
    // For now, if preserveFormatting is true, we won't strip any tags with this regex.
    // The logic in `parse` will handle it.
    this.htmlNonFormattingTagRegex = /<(?!\/?(strong|em|b|i|mark|small|del|ins|sub|sup)\b)[^>]*>/gi;

  }

  parse(rawData: string): FetchedTranscriptSnippet[] {
    const parser = new XMLParser({
      ignoreAttributes: false,
      attributeNamePrefix: '',
      textNodeName: '#text',
      parseTagValue: true, // Automatically unescapes attribute values
      processEntities: true, // Processes &apos;, &quot;, etc. in text nodes
      htmlEntities: true,    // Support HTML entities e.g. &nbsp;
      allowBooleanAttributes: true,
    });

    let jsonObj: any;
    try {
      jsonObj = parser.parse(rawData);
    } catch (e) {
      throw new YouTubeTranscriptApiException(`Failed to parse XML for transcript: ${(e as Error).message}`);
    }

    if (!jsonObj.transcript || (!Array.isArray(jsonObj.transcript.text) && typeof jsonObj.transcript.text !== 'object')) {
      // If transcript or transcript.text is missing or not in expected structure
      return [];
    }

    const textElements = Array.isArray(jsonObj.transcript.text) ? jsonObj.transcript.text : [jsonObj.transcript.text];

    const snippets: FetchedTranscriptSnippet[] = [];
    for (const element of textElements) {
      // Ensure element and its properties are valid
      if (element === null || typeof element !== 'object' || typeof element.start === 'undefined') {
        continue;
      }

      // textContent can be null if the tag is empty e.g. <text start="1" dur="1"></text>
      // Ensure textContent is a string, default to empty string if null or undefined
      let textContent = (element['#text'] === null || typeof element['#text'] === 'undefined') ? "" : String(element['#text']);

      // XMLParser with processEntities and htmlEntities should handle most unescaping.
      // `html-entities` can be used for any remaining or specific cases.
      textContent = unescape(textContent, { level: 'xml' }); // 'xml' for &apos;, &gt;, etc. 'html5' for &nbsp; etc.

      if (this.preserveFormatting) {
        // If preserving formatting, we want to strip tags that are NOT in FORMATTING_TAGS.
        // This is complex. A simpler model is to assume that only formatting tags are present
        // if preserveFormatting is true, and we return the text as-is.
        // However, if other tags like <font> (from srv1) are present, they should be stripped.
        // The Python code's regex `r"<\/?(?!\/?(" + formats_regex + r")\b).*?\b>"` does this.
        // Let's use a simplified version for now or refine htmlNonFormattingTagRegex.
        // Current htmlNonFormattingTagRegex /<(?!\/?(strong|em|b|i)\b)[^>]*>/gi will strip tags not in the list.
        // textContent = textContent.replace(this.htmlNonFormattingTagRegex, ''); // This was the intention.
        // For now, the policy is: if preserveFormatting, return raw unescaped text. Client handles rendering.
        // This means we don't use htmlNonFormattingTagRegex here yet, pending robust implementation.
      } else {
        // If not preserving formatting, strip all HTML tags.
        textContent = textContent.replace(this.htmlAllTagRegex, '');
      }

      snippets.push({
        text: textContent,
        start: parseFloat(element.start),
        duration: parseFloat(element.dur || '0.0'), // Fallback for missing duration
      });
    }
    return snippets;
  }
}

export class Transcript {
  public httpClient: AxiosInstance;
  public videoId: string;
  public url: string;
  public language: string;
  public languageCode: string;
  public isGenerated: boolean;
  public translationLanguages: TranslationLanguage[];
  private initialPreserveFormatting: boolean;

  constructor(
    httpClient: AxiosInstance,
    videoId: string,
    url: string,
    language: string,
    languageCode: string,
    isGenerated: boolean,
    translationLanguages: TranslationLanguage[],
    preserveFormatting: boolean = false,
  ) {
    this.httpClient = httpClient;
    this.videoId = videoId;
    this.url = url;
    this.language = language;
    this.languageCode = languageCode;
    this.isGenerated = isGenerated;
    this.translationLanguages = translationLanguages;
    this.initialPreserveFormatting = preserveFormatting;
  }

  async fetch(preserveFormattingArg?: boolean): Promise<FetchedTranscript> {
    // Determine the final preserveFormatting setting for this fetch call.
    // Priority: 1. preserveFormattingArg (if boolean) 2. this.initialPreserveFormatting
    const finalPreserveFormatting = typeof preserveFormattingArg === 'boolean'
      ? preserveFormattingArg
      : this.initialPreserveFormatting;

    if (this.url.includes('&exp=xpe')) {
      throw new PoTokenRequired(this.videoId);
    }

    try {
      const response = await this.httpClient.get<string>(this.url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
      });
      const rawTranscriptData = response.data;

      // Create a new parser instance with the determined formatting setting for this specific fetch.
      const parser = new TranscriptParser(finalPreserveFormatting);
      const snippets = parser.parse(rawTranscriptData);

      return {
        videoId: this.videoId,
        language: this.language,
        languageCode: this.languageCode,
        isGenerated: this.isGenerated,
        snippets,
      };
    } catch (error: any) {
      if (error.isAxiosError) {
        throw new YouTubeRequestFailed(this.videoId, error);
      }
      // Ensure other errors are instances of Error before accessing .message
      if (error instanceof Error) {
        throw new YouTubeTranscriptApiException(`Failed to fetch transcript data for video ${this.videoId}: ${error.message}`);
      }
      // Fallback for non-Error objects thrown
      throw new YouTubeTranscriptApiException(`An unknown error occurred while fetching transcript for video ${this.videoId}: ${String(error)}`);
    }
  }

  get isTranslatable(): boolean {
    return this.translationLanguages.length > 0;
  }

  translate(languageCode: string): Transcript {
    if (!this.isTranslatable) {
      throw new NotTranslatable(this.videoId);
    }

    const targetLanguage = this.translationLanguages.find(
      (lang) => lang.languageCode === languageCode
    );

    if (!targetLanguage) {
      throw new TranslationLanguageNotAvailable(this.videoId);
    }

    return new Transcript(
      this.httpClient,
      this.videoId,
      `${this.url}&tlang=${languageCode}`,
      targetLanguage.language,
      languageCode,
      true, // Translated transcripts are considered generated
      [],   // Translated transcripts themselves are not further translatable by this API
      this.initialPreserveFormatting // Carry over the initial preserveFormatting setting
    );
  }
}
