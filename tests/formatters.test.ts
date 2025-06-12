import {
  JSONFormatter,
  PrettyPrintFormatter,
  TextFormatter,
  SRTFormatter,
  WebVTTFormatter,
  FormatterLoader,
  UnknownFormatterType,
  Formatter,
} from '../src/formatters';
import { FetchedTranscript, FetchedTranscriptSnippet } from '../src/types';

const MOCK_VIDEO_ID = 'testVid';
const MOCK_LANGUAGE = 'English';
const MOCK_LANGUAGE_CODE = 'en';
const MOCK_IS_GENERATED = false;

const sampleSnippets: FetchedTranscriptSnippet[] = [
  { text: 'Hello world,', start: 0.123, duration: 1.456 },
  { text: 'this is a test transcript.', start: 1.579, duration: 2.345 },
  { text: 'Third line here.', start: 3.924, duration: 1.000 },
  { text: 'A line with "quotes" & special chars < >', start: 5.000, duration: 2.000 },
];

const sampleTranscript: FetchedTranscript = {
  videoId: MOCK_VIDEO_ID,
  language: MOCK_LANGUAGE,
  languageCode: MOCK_LANGUAGE_CODE,
  isGenerated: MOCK_IS_GENERATED,
  snippets: sampleSnippets,
};

const sampleSnippetsForOverlap: FetchedTranscriptSnippet[] = [
    { text: 'First line.', start: 0.100, duration: 1.500 }, // Ends at 1.600
    { text: 'Second line, starts early.', start: 1.200, duration: 1.000 }, // Starts at 1.200, ends at 2.200
    { text: 'Third line.', start: 2.500, duration: 1.000 }, // Starts at 2.500
];

const sampleTranscriptForOverlap: FetchedTranscript = {
    ...sampleTranscript,
    snippets: sampleSnippetsForOverlap,
};


describe('Formatters', () => {
  describe('JSONFormatter', () => {
    const formatter = new JSONFormatter();
    it('should format a single transcript to JSON', () => {
      const result = formatter.formatTranscript(sampleTranscript);
      expect(JSON.parse(result)).toEqual(sampleSnippets);
    });
    it('should format multiple transcripts to JSON', () => {
      const result = formatter.formatTranscripts([sampleTranscript, sampleTranscript]);
      const parsed = JSON.parse(result);
      expect(parsed).toBeInstanceOf(Array);
      expect(parsed.length).toBe(2);
      expect(parsed[0]).toEqual(sampleSnippets);
    });
  });

  describe('PrettyPrintFormatter', () => {
    const formatter = new PrettyPrintFormatter();
    it('should format a single transcript to pretty JSON', () => {
      const result = formatter.formatTranscript(sampleTranscript, { indent: 2 });
      // Check if it's valid JSON and roughly matches stringified with indent
      expect(JSON.parse(result)).toEqual(sampleSnippets);
      expect(result).toContain('\n  '); // Indicates indentation
    });
    it('should format multiple transcripts to pretty JSON', () => {
      const result = formatter.formatTranscripts([sampleTranscript, sampleTranscript], { indent: 2 });
      const parsed = JSON.parse(result);
      expect(parsed.length).toBe(2);
      expect(parsed[0]).toEqual(sampleSnippets);
      expect(result).toContain('\n  ');
    });
  });

  describe('TextFormatter', () => {
    const formatter = new TextFormatter();
    it('should format a single transcript to plain text', () => {
      const result = formatter.formatTranscript(sampleTranscript);
      const expected =
        'Hello world,\n' +
        'this is a test transcript.\n' +
        'Third line here.\n' +
        'A line with "quotes" & special chars < >';
      expect(result).toBe(expected);
    });
    it('should format multiple transcripts to plain text', () => {
      const single =
        'Hello world,\n' +
        'this is a test transcript.\n' +
        'Third line here.\n' +
        'A line with "quotes" & special chars < >';
      const result = formatter.formatTranscripts([sampleTranscript, sampleTranscript]);
      expect(result).toBe(`${single}\n\n\n${single}`);
    });
  });

  describe('SRTFormatter', () => {
    const formatter = new SRTFormatter();
    it('should format a single transcript to SRT', () => {
      const result = formatter.formatTranscript(sampleTranscript);
      const expected =
        '1\n00:00:00,123 --> 00:00:01,579\nHello world,\n\n' + // Ends at start of next
        '2\n00:00:01,579 --> 00:00:03,924\nthis is a test transcript.\n\n' +
        '3\n00:00:03,924 --> 00:00:04,924\nThird line here.\n\n' +
        '4\n00:00:05,000 --> 00:00:07,000\nA line with "quotes" & special chars < >\n';
      expect(result).toBe(expected);
    });

    it('should handle overlapping snippet end times correctly in SRT', () => {
        const formatter = new SRTFormatter();
        const result = formatter.formatTranscript(sampleTranscriptForOverlap);
        const expected =
          '1\n00:00:00,100 --> 00:00:01,200\nFirst line.\n\n' + // End time adjusted to start of snippet 2
          '2\n00:00:01,200 --> 00:00:02,200\nSecond line, starts early.\n\n' +
          '3\n00:00:02,500 --> 00:00:03,500\nThird line.\n';
        expect(result).toBe(expected);
    });
  });

  describe('WebVTTFormatter', () => {
    const formatter = new WebVTTFormatter();
    it('should format a single transcript to WebVTT', () => {
      const result = formatter.formatTranscript(sampleTranscript);
      const expected =
        'WEBVTT\n\n' +
        '00:00:00.123 --> 00:00:01.579\nHello world,\n\n' + // Ends at start of next
        '00:00:01.579 --> 00:00:03.924\nthis is a test transcript.\n\n' +
        '00:00:03.924 --> 00:00:04.924\nThird line here.\n\n' +
        '00:00:05.000 --> 00:00:07.000\nA line with "quotes" & special chars < >\n';
      expect(result).toBe(expected);
    });

    it('should handle overlapping snippet end times correctly in WebVTT', () => {
        const formatter = new WebVTTFormatter();
        const result = formatter.formatTranscript(sampleTranscriptForOverlap);
        const expected =
          'WEBVTT\n\n' +
          '00:00:00.100 --> 00:00:01.200\nFirst line.\n\n' + // End time adjusted to start of snippet 2
          '00:00:01.200 --> 00:00:02.200\nSecond line, starts early.\n\n' +
          '00:00:02.500 --> 00:00:03.500\nThird line.\n';
        expect(result).toBe(expected);
    });
  });

  describe('FormatterLoader', () => {
    const loader = new FormatterLoader();
    it('should load JSONFormatter', () => {
      expect(loader.load('json')).toBeInstanceOf(JSONFormatter);
    });
    it('should load PrettyPrintFormatter', () => {
      expect(loader.load('pretty')).toBeInstanceOf(PrettyPrintFormatter);
    });
    it('should load TextFormatter', () => {
      expect(loader.load('text')).toBeInstanceOf(TextFormatter);
    });
    it('should load SRTFormatter', () => {
      expect(loader.load('srt')).toBeInstanceOf(SRTFormatter);
    });
    it('should load WebVTTFormatter', () => {
      expect(loader.load('webvtt')).toBeInstanceOf(WebVTTFormatter);
    });
    it('should default to PrettyPrintFormatter if no type is specified', () => {
      expect(loader.load()).toBeInstanceOf(PrettyPrintFormatter);
    });
    it('should be case-insensitive for formatter types', () => {
      expect(loader.load('SRT')).toBeInstanceOf(SRTFormatter);
      expect(loader.load('Json')).toBeInstanceOf(JSONFormatter);
    });
    it('should throw UnknownFormatterType for an invalid type', () => {
      expect(() => loader.load('xml')).toThrow(UnknownFormatterType);
      expect(() => loader.load('xml')).toThrow(
        "The format 'xml' is not supported. Choose one of the following formats: json, pretty, text, webvtt, srt"
      );
    });
  });
});
