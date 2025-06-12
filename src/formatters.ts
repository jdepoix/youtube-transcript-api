import { FetchedTranscript, FetchedTranscriptSnippet } from './types';

export interface Formatter {
  formatTranscript(transcript: FetchedTranscript, options?: any): string;
  formatTranscripts(transcripts: FetchedTranscript[], options?: any): string;
}

export class PrettyPrintFormatter implements Formatter {
  formatTranscript(transcript: FetchedTranscript, options: { indent?: number } = {}): string {
    const indent = options.indent === undefined ? 2 : options.indent; // Default indent to 2 for pretty printing
    return JSON.stringify(transcript.snippets, null, indent);
  }

  formatTranscripts(transcripts: FetchedTranscript[], options: { indent?: number } = {}): string {
    const indent = options.indent === undefined ? 2 : options.indent;
    return JSON.stringify(
      transcripts.map(transcript => transcript.snippets),
      null,
      indent
    );
  }
}

export class JSONFormatter implements Formatter {
  formatTranscript(transcript: FetchedTranscript, options?: any): string {
    // `options` could be used for `JSON.stringify` replacer or space arguments if needed
    return JSON.stringify(transcript.snippets, null, options?.space);
  }

  formatTranscripts(transcripts: FetchedTranscript[], options?: any): string {
    return JSON.stringify(
      transcripts.map(transcript => transcript.snippets),
      null,
      options?.space
    );
  }
}

export class TextFormatter implements Formatter {
  formatTranscript(transcript: FetchedTranscript, options?: any): string {
    return transcript.snippets.map(line => line.text).join('\n');
  }

  formatTranscripts(transcripts: FetchedTranscript[], options?: any): string {
    return transcripts
      .map(transcript => this.formatTranscript(transcript, options))
      .join('\n\n\n');
  }
}

abstract class TextBasedFormatter extends TextFormatter {
  protected abstract formatTimestamp(hours: number, mins: number, secs: number, ms: number): string;

  protected abstract formatTranscriptHeader(lines: string[]): string;

  protected abstract formatTranscriptHelper(
    index: number,
    timeText: string,
    snippet: FetchedTranscriptSnippet,
  ): string;

  protected secondsToTimestamp(time: number): string {
    const hours = Math.floor(time / 3600);
    const minutes = Math.floor((time % 3600) / 60);
    const seconds = Math.floor(time % 60);
    const milliseconds = Math.round((time - Math.floor(time)) * 1000);
    return this.formatTimestamp(hours, minutes, seconds, milliseconds);
  }

  formatTranscript(transcript: FetchedTranscript, options?: any): string {
    const lines: string[] = [];
    transcript.snippets.forEach((line, i) => {
      const end = line.start + line.duration;
      // In Python: transcript[i + 1].start if i < len(transcript) - 1 and transcript[i + 1].start < end else end
      // This logic ensures the end timestamp doesn't exceed the start of the next snippet if they overlap/are too close.
      let actualEnd = end;
      if (i < transcript.snippets.length - 1) {
          const nextSnippetStart = transcript.snippets[i+1].start;
          if (nextSnippetStart < end) {
              actualEnd = nextSnippetStart;
          }
      }

      const timeText = `${this.secondsToTimestamp(line.start)} --> ${this.secondsToTimestamp(actualEnd)}`;
      lines.push(this.formatTranscriptHelper(i, timeText, line));
    });
    return this.formatTranscriptHeader(lines);
  }
}

export class SRTFormatter extends TextBasedFormatter {
  protected formatTimestamp(hours: number, mins: number, secs: number, ms: number): string {
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
  }

  protected formatTranscriptHeader(lines: string[]): string {
    return lines.join('\n\n') + '\n';
  }

  protected formatTranscriptHelper(
    index: number,
    timeText: string,
    snippet: FetchedTranscriptSnippet,
  ): string {
    return `${index + 1}\n${timeText}\n${snippet.text}`;
  }
}

export class WebVTTFormatter extends TextBasedFormatter {
  protected formatTimestamp(hours: number, mins: number, secs: number, ms: number): string {
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
  }

  protected formatTranscriptHeader(lines: string[]): string {
    return 'WEBVTT\n\n' + lines.join('\n\n') + '\n';
  }

  protected formatTranscriptHelper(
    index: number, // WebVTT doesn't use an index per cue by default, but helper expects it
    timeText: string,
    snippet: FetchedTranscriptSnippet,
  ): string {
    // Original Python WebVTT did not include index in the output, only time_text and snippet.text
    return `${timeText}\n${snippet.text}`;
  }
}

export class UnknownFormatterType extends Error {
  constructor(formatterType: string) {
    super(
      `The format '${formatterType}' is not supported. ` +
      `Choose one of the following formats: ${Object.keys(FormatterLoader.TYPES).join(', ')}`
    );
    this.name = 'UnknownFormatterType';
  }
}

export class FormatterLoader {
  public static readonly TYPES: Record<string, { new(): Formatter }> = {
    json: JSONFormatter,
    pretty: PrettyPrintFormatter,
    text: TextFormatter,
    webvtt: WebVTTFormatter,
    srt: SRTFormatter,
  };

  public load(formatterType: string = 'pretty'): Formatter {
    const FormatterClass = FormatterLoader.TYPES[formatterType.toLowerCase()];
    if (!FormatterClass) {
      throw new UnknownFormatterType(formatterType);
    }
    return new FormatterClass();
  }
}
