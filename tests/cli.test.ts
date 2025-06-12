import fs from 'fs';
import { YouTubeTranscriptApi } from '../src/youtube-transcript-api';
import { FormatterLoader } from '../src/formatters'; // Used for choices
import { TranscriptList } from '../src/transcript-list-fetcher';
import { Transcript } from '../src/transcript';
import { FetchedTranscript, FetchedTranscriptSnippet } from '../src/types';
import { NoTranscriptFound, TranscriptsDisabled } from '../src/errors';

// Mock the main API module
jest.mock('../src/youtube-transcript-api');
const MockedYouTubeTranscriptApi = YouTubeTranscriptApi as jest.MockedClass<typeof YouTubeTranscriptApi>;

// Mock fs module
jest.mock('fs');
const mockedFs = fs as jest.Mocked<typeof fs>;

// Store original console methods
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

// Capture console output
let consoleOutput: string[] = [];
let consoleErrorOutput: string[] = [];

// Helper function to run the CLI's main function programmatically
// yargs is tricky to test by directly calling its parse method with arguments array.
// A common pattern is to refactor cli.ts to export its main logic/handler function
// that yargs would call, then test that function.
// For now, we'll set up process.argv and require the module to run.
// This is more of an integration test for the CLI.

const runCli = async (args: string[]): Promise<{ logs: string[]; errors: string[]; exitCode: number | null }> => {
  const oldArgv = process.argv;
  process.argv = ['node', 'cli.js', ...args]; // Mock process.argv

  let exitCode: number | null = null;
  const originalProcessExit = process.exit;
  process.exit = ((code?: number) => { // Mock process.exit
    exitCode = code === undefined ? 0 : code;
    // Don't actually exit during tests
  }) as any;


  consoleOutput = []; // Reset captures
  consoleErrorOutput = [];

  try {
    // Dynamically import to re-run the script with new argv
    // jest.resetModules() ensures a fresh import if cli.ts has top-level execution
    jest.resetModules();
    await import('../src/cli'); // cli.ts has a main().catch() structure
    // Wait for any async operations within cli.ts to complete if possible
    await new Promise(resolve => setImmediate(resolve));
  } catch (e) {
    // This catch might not be hit if cli.ts itself catches all errors and process.exit()
    // consoleErrorOutput.push(String(e));
  } finally {
    process.argv = oldArgv; // Restore original argv
    process.exit = originalProcessExit; // Restore original process.exit
  }
  return { logs: consoleOutput, errors: consoleErrorOutput, exitCode };
};


describe('CLI Tests', () => {
  let mockApiInstance: jest.Mocked<YouTubeTranscriptApi>;

  beforeEach(() => {
    // Reset mocks for each test
    MockedYouTubeTranscriptApi.mockClear();
    mockedFs.writeFileSync.mockClear();

    // Mock console methods
    console.log = jest.fn(message => consoleOutput.push(String(message)));
    console.error = jest.fn(message => consoleErrorOutput.push(String(message)));

    // Setup the mock implementation for the API constructor and its methods
    // This is a default mock that can be overridden in specific tests
    mockApiInstance = {
      list: jest.fn(),
      fetch: jest.fn(),
    } as unknown as jest.Mocked<YouTubeTranscriptApi>;
    MockedYouTubeTranscriptApi.mockImplementation(() => mockApiInstance);
  });

  afterEach(() => {
    // Restore original console methods
    console.log = originalConsoleLog;
    console.error = originalConsoleError;
  });

  const MOCK_VIDEO_ID = 'testVidCLI';
  const sampleSnippets: FetchedTranscriptSnippet[] = [{ text: 'Hello', start: 0, duration: 1 }];
  const mockFetchedTranscript: FetchedTranscript = { videoId: MOCK_VIDEO_ID, language: 'English', languageCode: 'en', isGenerated: false, snippets: sampleSnippets };

  // Mock Transcript instance (simplified)
  const mockTranscriptInstance = {
    videoId: MOCK_VIDEO_ID,
    language: 'English',
    languageCode: 'en',
    isGenerated: false,
    translationLanguages: [{ language: 'German', languageCode: 'de' }],
    url: 'testUrl',
    fetch: jest.fn().mockResolvedValue(mockFetchedTranscript),
    translate: jest.fn().mockImplementation(function(this: Transcript, langCode: string) {
        // Return a new "translated" transcript-like object
        return { ...this, languageCode: langCode, url: this.url + `&tlang=${langCode}`, fetch: jest.fn().mockResolvedValue({...mockFetchedTranscript, languageCode: langCode}) };
    }),
    isTranslatable: true,
  } as unknown as Transcript;

  const mockTranscriptList = {
    videoId: MOCK_VIDEO_ID,
    manuallyCreatedTranscripts: { 'en': mockTranscriptInstance },
    generatedTranscripts: { 'de': { ...mockTranscriptInstance, languageCode: 'de', isGenerated: true } as Transcript },
    translationLanguages: [{ language: 'Spanish', languageCode: 'es' }],
    findTranscript: jest.fn().mockReturnValue(mockTranscriptInstance),
    findManuallyCreatedTranscript: jest.fn().mockReturnValue(mockTranscriptInstance),
    findGeneratedTranscript: jest.fn().mockReturnValue(mockTranscriptInstance),
    [Symbol.iterator]: jest.fn(function* () {
        yield mockTranscriptInstance;
        yield ({ ...mockTranscriptInstance, languageCode: 'de', isGenerated: true } as Transcript);
    }),
    toString: jest.fn().mockReturnValue(`TranscriptList for ${MOCK_VIDEO_ID}:\n - en ("English")\n - de ("German") (generated)`),
  } as unknown as TranscriptList;


  it('should fetch transcript and print to console with default formatter (pretty)', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);
    // fetch on the mockTranscriptInstance is already mocked

    await runCli([MOCK_VIDEO_ID]);

    expect(MockedYouTubeTranscriptApi).toHaveBeenCalledTimes(1);
    expect(mockApiInstance.list).toHaveBeenCalledWith(MOCK_VIDEO_ID);
    expect(mockTranscriptList.findTranscript).toHaveBeenCalledWith(['en']); // Default language
    expect(mockTranscriptInstance.fetch).toHaveBeenCalled();
    expect(consoleOutput.join('\n')).toContain(JSON.stringify(sampleSnippets, null, 2)); // Pretty format
  });

  it('should use specified formatter (e.g., srt)', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);

    await runCli([MOCK_VIDEO_ID, '--format', 'srt']);

    expect(consoleOutput.join('\n')).toContain('1\n00:00:00,000 --> 00:00:01,000\nHello'); // SRT format
  });

  it('should list available transcripts with --list-transcripts', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);

    await runCli([MOCK_VIDEO_ID, '--list-transcripts']);

    expect(mockApiInstance.list).toHaveBeenCalledWith(MOCK_VIDEO_ID);
    expect(mockTranscriptList.toString).toHaveBeenCalled();
    expect(consoleOutput.join('\n')).toContain(`TranscriptList for ${MOCK_VIDEO_ID}`);
  });

  it('should handle language selection with --languages', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);

    await runCli([MOCK_VIDEO_ID, '--languages', 'de', 'en']);

    expect(mockTranscriptList.findTranscript).toHaveBeenCalledWith(['de', 'en']);
  });

  it('should write output to file with --output-file', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);

    await runCli([MOCK_VIDEO_ID, '--output-file', 'output.txt']);

    expect(mockedFs.writeFileSync).toHaveBeenCalledWith('output.txt', expect.any(String));
    expect(consoleOutput.join('\n')).toContain('Output successfully written to output.txt');
  });

  it('should pass proxy config to YouTubeTranscriptApi', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);

    await runCli([MOCK_VIDEO_ID, '--http-proxy', 'http://myproxy:8080']);

    expect(MockedYouTubeTranscriptApi).toHaveBeenCalledWith(
      expect.objectContaining({ host: 'myproxy', port: 8080, protocol: 'http' })
    );
  });

  it('should handle --translate option', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);
    // The translate method on mockTranscriptInstance is already mocked
    // Its fetch method is also mocked to return a "translated" transcript

    await runCli([MOCK_VIDEO_ID, '--languages', 'en', '--translate', 'de']);

    expect(mockTranscriptList.findTranscript).toHaveBeenCalledWith(['en']);
    expect(mockTranscriptInstance.translate).toHaveBeenCalledWith('de');
    // Check if the "translated" snippets are printed (mocked to be same as original but with diff lang code)
    const translatedMockResponse = { ...mockFetchedTranscript, languageCode: 'de' };
    expect(consoleOutput.join('\n')).toContain(JSON.stringify(translatedMockResponse.snippets, null, 2));
  });

  it('should use findGeneratedTranscript with --exclude-manually-created', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);

    await runCli([MOCK_VIDEO_ID, '--exclude-manually-created']);

    expect(mockTranscriptList.findGeneratedTranscript).toHaveBeenCalledWith(['en']);
  });

  it('should use findManuallyCreatedTranscript with --exclude-generated', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);

    await runCli([MOCK_VIDEO_ID, '--exclude-generated']);

    expect(mockTranscriptList.findManuallyCreatedTranscript).toHaveBeenCalledWith(['en']);
  });

  it('should print error if API throws NoTranscriptFound', async () => {
    mockApiInstance.list.mockResolvedValue(mockTranscriptList);
    mockTranscriptList.findTranscript.mockImplementation(() => {
      throw new NoTranscriptFound(MOCK_VIDEO_ID, 'es', mockTranscriptList);
    });

    await runCli([MOCK_VIDEO_ID, '--languages', 'es']);

    expect(consoleErrorOutput.join('\n')).toContain(`Could not find a transcript for video ${MOCK_VIDEO_ID} in the requested languages: es`);
  });

  it('should print error if API throws TranscriptsDisabled', async () => {
    mockApiInstance.list.mockImplementation(() => {
      throw new TranscriptsDisabled(MOCK_VIDEO_ID);
    });

    await runCli([MOCK_VIDEO_ID]);

    expect(consoleErrorOutput.join('\n')).toContain(`Subtitles are disabled for this video: ${MOCK_VIDEO_ID}`);
  });

  it('should exit with code 0 if --exclude-manually-created and --exclude-generated are both set', async () => {
    const { exitCode } = await runCli([MOCK_VIDEO_ID, '--exclude-manually-created', '--exclude-generated']);
    expect(exitCode).toBe(0);
    expect(consoleOutput.join('\n')).toBe(''); // Python CLI prints empty string
  });

});
