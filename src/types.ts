export interface FetchedTranscriptSnippet {
  text: string;
  start: number; // float in Python corresponds to number in TypeScript
  duration: number; // float in Python corresponds to number in TypeScript
}

export interface FetchedTranscript {
  snippets: FetchedTranscriptSnippet[];
  videoId: string;
  language: string;
  languageCode: string;
  isGenerated: boolean;
}

export interface TranslationLanguage {
  language: string;
  languageCode: string;
}
