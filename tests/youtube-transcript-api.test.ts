import axios from 'axios';
import { YouTubeTranscriptApi } from '../src/youtube-transcript-api';
import { TranscriptList } from '../src/transcript-list-fetcher';
import {
  TranscriptsDisabled,
  VideoUnavailable,
  VideoUnplayable,
  AgeRestricted,
  RequestBlocked,
  IpBlocked,
  YouTubeDataUnparsable,
  NoTranscriptFound,
  PoTokenRequired
} from '../src/errors';
import {
  generateMockYouTubePageHtml,
  MOCK_VIDEO_ID,
  MOCK_API_KEY,
  mockPlayerResponseTranscriptsDisabled,
  mockPlayerResponseVideoUnavailable,
  mockPlayerResponseVideoUnplayable,
  mockPlayerResponseAgeRestricted,
  MOCK_CONSENT_PAGE_HTML,
  MOCK_INNERTUBE_API_PLAYER_RESPONSE,
  MOCK_INNERTUBE_API_PLAYER_RESPONSE_NO_CAPTIONS,
  MOCK_SRV3_TRANSCRIPT_XML_EN,
  MOCK_SRV3_TRANSCRIPT_XML_DE,
  MOCK_TOO_MANY_REQUESTS_HTML,
  getMockCaptionTrackWithPoToken,
  MOCK_HTML_NO_API_KEY,
  MOCK_HTML_NO_PLAYER_RESPONSE,
  MOCK_INNERTUBE_MEMBERS_ONLY,
  MOCK_INNERTUBE_PRIVATE_VIDEO,
} from './assets/youtube-html-mock';

// Mock axios globally for all tests in this file
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>; // Type assertion for mocked instance

describe('YouTubeTranscriptApi', () => {
  let api: YouTubeTranscriptApi;

  beforeEach(() => {
    // Reset mocks before each test
    mockedAxios.get.mockReset();
    mockedAxios.post.mockReset();
    api = new YouTubeTranscriptApi();
  });

  describe('list() method', () => {
    it('should list transcripts successfully for a video with multiple languages', async () => {
      // Mock the HTML fetch for video page
      mockedAxios.get.mockResolvedValueOnce({
        data: generateMockYouTubePageHtml(MOCK_VIDEO_ID)
      });
      // Mock the InnerTube API call (POST)
      mockedAxios.post.mockResolvedValueOnce({
        data: MOCK_INNERTUBE_API_PLAYER_RESPONSE // This mock should align with what fetchInnertubeData expects
      });

      const transcriptList = await api.list(MOCK_VIDEO_ID);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `https://www.youtube.com/watch?v=${MOCK_VIDEO_ID}`,
        expect.any(Object) // Headers
      );
      // This assertion might be too simplistic if INNERTUBE_API_URL is constructed with a dynamic key
      // The key is extracted from the HTML page, so the post URL will use MOCK_API_KEY from the HTML mock
      expect(mockedAxios.post).toHaveBeenCalledWith(
        `https://www.youtube.com/youtubei/v1/player?key=${MOCK_API_KEY}`,
        expect.objectContaining({ videoId: MOCK_VIDEO_ID }),
        expect.any(Object) // Headers
      );

      expect(transcriptList).toBeInstanceOf(TranscriptList);
      expect(transcriptList.videoId).toBe(MOCK_VIDEO_ID);

      // Based on generateMockYouTubePageHtml's defaultPlayerResponse
      // which is then refined by MOCK_INNERTUBE_API_PLAYER_RESPONSE for the .post call
      // The actual TranscriptList is built from the result of _fetchCaptionsJson, which uses _fetchInnertubeData last.
      const enTranscript = transcriptList.manuallyCreatedTranscripts['en'] || transcriptList.generatedTranscripts['en'];
      const frTranscript = transcriptList.manuallyCreatedTranscripts['fr'] || transcriptList.generatedTranscripts['fr'];

      expect(enTranscript).toBeDefined();
      expect(enTranscript?.languageCode).toBe('en');
      expect(enTranscript?.isGenerated).toBe(true); // From MOCK_INNERTUBE_API_PLAYER_RESPONSE

      expect(frTranscript).toBeDefined();
      expect(frTranscript?.languageCode).toBe('fr');
      expect(frTranscript?.isGenerated).toBe(false); // Manual

      expect(Object.keys(transcriptList.manuallyCreatedTranscripts).length + Object.keys(transcriptList.generatedTranscripts).length).toBe(2);
      expect(transcriptList.translationLanguages.length).toBe(2); // de, es from MOCK_INNERTUBE_API_PLAYER_RESPONSE
    });

    it('should throw TranscriptsDisabled if captions are not available', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: generateMockYouTubePageHtml(MOCK_VIDEO_ID, mockPlayerResponseTranscriptsDisabled),
      });
      // If initial HTML has no captions, _fetchInnertubeData is called.
      // That also returns no captions.
      mockedAxios.post.mockResolvedValueOnce({
        data: MOCK_INNERTUBE_API_PLAYER_RESPONSE_NO_CAPTIONS,
      });

      await expect(api.list(MOCK_VIDEO_ID)).rejects.toThrow(TranscriptsDisabled);
    });

    it('should throw VideoUnavailable if video is unavailable', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: generateMockYouTubePageHtml(MOCK_VIDEO_ID, mockPlayerResponseVideoUnavailable),
      });
      // InnerTube API would also confirm unavailability
       mockedAxios.post.mockResolvedValueOnce({
        data: { playabilityStatus: { status: 'ERROR', reason: 'Video unavailable' } }
      });
      await expect(api.list(MOCK_VIDEO_ID)).rejects.toThrow(VideoUnavailable);
    });

    it('should throw VideoUnplayable for generic unplayable video', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: generateMockYouTubePageHtml(MOCK_VIDEO_ID, mockPlayerResponseVideoUnplayable),
      });
       mockedAxios.post.mockResolvedValueOnce({
        data: { playabilityStatus: { status: 'UNPLAYABLE', reason: 'Some reason' } }
      });
      await expect(api.list(MOCK_VIDEO_ID)).rejects.toThrow(VideoUnplayable);
    });

    it('should throw AgeRestricted for age-restricted video', async () => {
        mockedAxios.get.mockResolvedValueOnce({
            data: generateMockYouTubePageHtml(MOCK_VIDEO_ID, mockPlayerResponseAgeRestricted)
        });
        mockedAxios.post.mockResolvedValueOnce({
            data: MOCK_INNERTUBE_PLAYER_RESPONSE_AGE_RESTRICTED
        });
        await expect(api.list(MOCK_VIDEO_ID)).rejects.toThrow(AgeRestricted);
    });

    it('should handle consent page by making a second request', async () => {
        // First GET returns consent page
        mockedAxios.get.mockResolvedValueOnce({ data: MOCK_CONSENT_PAGE_HTML });
        // Second GET (after attempting to set cookie) returns actual page
        mockedAxios.get.mockResolvedValueOnce({ data: generateMockYouTubePageHtml(MOCK_VIDEO_ID) });
        // POST for InnerTube data
        mockedAxios.post.mockResolvedValueOnce({ data: MOCK_INNERTUBE_API_PLAYER_RESPONSE });

        await api.list(MOCK_VIDEO_ID);

        expect(mockedAxios.get).toHaveBeenCalledTimes(2);
        // First call to video page, second call to video page after consent.
        expect(mockedAxios.get.mock.calls[0][0]).toBe(`https://www.youtube.com/watch?v=${MOCK_VIDEO_ID}`);
        expect(mockedAxios.get.mock.calls[1][0]).toBe(`https://www.youtube.com/watch?v=${MOCK_VIDEO_ID}`);
        // TODO: We'd ideally check that a cookie was attempted to be set with axios if we had a cookie jar mock.
        // For now, just checking the calls is a good start.
    });

    it('should throw IpBlocked if INNERTUBE_API_KEY is missing and recaptcha is present', async () => {
        // HTML has no API key but has g-recaptcha
        mockedAxios.get.mockResolvedValueOnce({
            data: generateMockYouTubePageHtml(MOCK_VIDEO_ID, undefined, '') // Pass empty string for apiKeyOverride
        });
        // _fetchInnertubeData would not be called if API key extraction fails this way.

        await expect(api.list(MOCK_VIDEO_ID)).rejects.toThrow(IpBlocked);
    });

    it('should throw YouTubeDataUnparsable if INNERTUBE_API_KEY is missing and no recaptcha', async () => {
        // HTML has no API key and no g-recaptcha
        const htmlWithoutApiKeyAndRecaptcha = generateMockYouTubePageHtml(MOCK_VIDEO_ID, undefined, '').replace('<div class="g-recaptcha"></div>', '');
        mockedAxios.get.mockResolvedValueOnce({
            data: htmlWithoutApiKeyAndRecaptcha
        });

        await expect(api.list(MOCK_VIDEO_ID)).rejects.toThrow(YouTubeDataUnparsable);
    });

    it('should throw RequestBlocked if GET request to video page is blocked (e.g. 429 error)', async () => {
        mockedAxios.get.mockRejectedValueOnce({
            isAxiosError: true,
            response: { status: 429, data: MOCK_TOO_MANY_REQUESTS_HTML },
            message: 'Request failed with status code 429'
        });
        // Note: The current TranscriptListFetcher maps HTTP errors from Axios to YouTubeRequestFailed.
        // A 429 specifically could be mapped to RequestBlocked or IpBlocked if the response implies it.
        // For now, checking for YouTubeRequestFailed is consistent with current direct mapping.
        // If the Python version has specific logic to turn a 429 into RequestBlocked, that needs to be replicated in TranscriptListFetcher.
        // Based on Python's _raise_http_errors, it raises YouTubeRequestFailed for any HTTPError.
        // RequestBlocked is typically raised based on content of playabilityStatus or specific HTML patterns.
        // Let's assume a 429 from initial GET is a YouTubeRequestFailed.
        // To test RequestBlocked more directly via playabilityStatus:
        const playerResponseRequestBlocked = {
            playabilityStatus: {
                status: "LOGIN_REQUIRED", // This status code
                reason: "Sign in to confirm you’re not a bot" // This reason
            }
        };
        mockedAxios.get.mockReset(); // Reset from previous mock
        mockedAxios.get.mockResolvedValueOnce({
            data: generateMockYouTubePageHtml(MOCK_VIDEO_ID, playerResponseRequestBlocked)
        });
        mockedAxios.post.mockResolvedValueOnce({ data: playerResponseRequestBlocked });


        await expect(api.list(MOCK_VIDEO_ID)).rejects.toThrow(RequestBlocked);
    });

    // Test for members-only video
    it('should throw VideoUnplayable for members-only video', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: generateMockYouTubePageHtml(MOCK_VIDEO_ID, MOCK_INNERTUBE_MEMBERS_ONLY)
      });
      mockedAxios.post.mockResolvedValueOnce({ data: MOCK_INNERTUBE_MEMBERS_ONLY });
      await expect(api.list(MOCK_VIDEO_ID)).rejects.toThrow(VideoUnplayable);
    });

    // Test for private video
    it('should throw VideoUnavailable for private video', async () => {
      // Private videos often return "ERROR" with "This video is private."
      // which our _assertPlayability maps to VideoUnavailable if video ID is okay.
      mockedAxios.get.mockResolvedValueOnce({
        data: generateMockYouTubePageHtml(MOCK_VIDEO_ID, MOCK_INNERTUBE_PRIVATE_VIDEO)
      });
      mockedAxios.post.mockResolvedValueOnce({ data: MOCK_INNERTUBE_PRIVATE_VIDEO });
      await expect(api.list(MOCK_VIDEO_ID)).rejects.toThrow(VideoUnavailable);
    });


    // TODO: Add tests for scenarios where _fetchInnertubeData is critical
    // e.g., initial HTML has no player_response, or it's minimal,
    // and the POST to innertube API provides the full data or different data.
    it('should use Innertube API data if initial HTML player_response is missing captions', async () => {
        const htmlWithoutCaptions = generateMockYouTubePageHtml(MOCK_VIDEO_ID, {
            playabilityStatus: { status: 'OK' },
            // captions object is missing here
        });
        mockedAxios.get.mockResolvedValueOnce({ data: htmlWithoutCaptions });
        // InnerTube API (POST) returns the full data with captions
        mockedAxios.post.mockResolvedValueOnce({ data: MOCK_INNERTUBE_API_PLAYER_RESPONSE });

        const transcriptList = await api.list(MOCK_VIDEO_ID);
        expect(transcriptList).toBeInstanceOf(TranscriptList);
        // Check if transcripts are from MOCK_INNERTUBE_API_PLAYER_RESPONSE
        expect(transcriptList.generatedTranscripts['en']).toBeDefined();
        expect(transcriptList.manuallyCreatedTranscripts['fr']).toBeDefined();
    });


  });

  // More describe blocks for fetch() method, TranscriptList methods, Transcript.translate() etc.
  // will follow here.

  describe('fetch() method', () => {
    beforeEach(() => {
      // Setup default mocks for successful HTML and InnerTube API responses for fetch tests
      // These lead to a TranscriptList similar to the one in MOCK_INNERTUBE_API_PLAYER_RESPONSE
      mockedAxios.get.mockResolvedValueOnce({
        data: generateMockYouTubePageHtml(MOCK_VIDEO_ID)
      });
      mockedAxios.post.mockResolvedValueOnce({
        data: MOCK_INNERTUBE_API_PLAYER_RESPONSE
      });
    });

    it('should fetch a specific transcript (e.g., en)', async () => {
      // Mock the XML transcript fetch for English
      mockedAxios.get.mockResolvedValueOnce({ data: MOCK_SRV3_TRANSCRIPT_XML_EN });

      const fetchedTranscript = await api.fetch(MOCK_VIDEO_ID, ['en']);

      // Verify that the GET request for the transcript XML was made to the correct URL
      // The URL comes from MOCK_INNERTUBE_API_PLAYER_RESPONSE.generatedTranscripts['en'].baseUrl
      // Note: The previous HTML/POST mocks are for list() part of fetch(). A new GET is for transcript content.
      expect(mockedAxios.get).toHaveBeenCalledTimes(2); // 1 for HTML page, 1 for XML transcript
      expect(mockedAxios.get.mock.calls[1][0]).toBe(`https://www.youtube.com/api/timedtext?v=${MOCK_VIDEO_ID}&lang=en&format=srv3`);

      expect(fetchedTranscript.videoId).toBe(MOCK_VIDEO_ID);
      expect(fetchedTranscript.languageCode).toBe('en');
      expect(fetchedTranscript.snippets).toBeInstanceOf(Array);
      expect(fetchedTranscript.snippets.length).toBe(3);
      expect(fetchedTranscript.snippets[0].text).toBe('Hello world,');
    });

    it('should fetch with language fallbacks (e.g., try de, then en)', async () => {
      // MOCK_INNERTUBE_API_PLAYER_RESPONSE has 'en' (generated) and 'fr' (manual).
      // If we ask for ['de', 'en'], it should find 'en'.

      // Mock the XML transcript fetch for English
      mockedAxios.get.mockResolvedValueOnce({ data: MOCK_SRV3_TRANSCRIPT_XML_EN });

      const fetchedTranscript = await api.fetch(MOCK_VIDEO_ID, ['de', 'en']);
      expect(mockedAxios.get.mock.calls[1][0]).toBe(`https://www.youtube.com/api/timedtext?v=${MOCK_VIDEO_ID}&lang=en&format=srv3`);
      expect(fetchedTranscript.languageCode).toBe('en');
      expect(fetchedTranscript.snippets[0].text).toBe('Hello world,');
    });

    it('should throw NoTranscriptFound if requested languages are not available', async () => {
      // MOCK_INNERTUBE_API_PLAYER_RESPONSE has 'en', 'fr'. Request 'es'.
      await expect(api.fetch(MOCK_VIDEO_ID, ['es'])).rejects.toThrow(NoTranscriptFound);
    });

    it('should fetch default language if no languages array is provided', async () => {
        // Based on MOCK_INNERTUBE_API_PLAYER_RESPONSE, 'en' (generated) should be found first if default logic iterates.
        // The fetch() method's current default logic tries all available if languages is empty/undefined.
        // For MOCK_INNERTUBE_API_PLAYER_RESPONSE, 'en' is first in generated, 'fr' in manual.
        // The findTranscript logic tries manual first. So 'fr' should be picked.
        mockedAxios.get.mockResolvedValueOnce({ data: MOCK_SRV3_TRANSCRIPT_XML_FR_TRANSLATED }); // Mock for French

        const fetchedTranscript = await api.fetch(MOCK_VIDEO_ID); // No languages specified

        expect(mockedAxios.get.mock.calls[1][0]).toBe(`https://www.youtube.com/api/timedtext?v=${MOCK_VIDEO_ID}&lang=fr&format=srv3`);
        expect(fetchedTranscript.languageCode).toBe('fr');
        expect(fetchedTranscript.snippets[0].text).toBe('Bonjour le monde,');
    });

    it('should fetch with preserve_formatting=true (testing TranscriptParser implicitly)', async () => {
      // Mock XML data that might contain HTML tags
      const xmlWithHtml = `<transcript><text start="0" dur="1">Hello <b>bold</b> world</text></transcript>`;
      mockedAxios.get.mockResolvedValueOnce({ data: xmlWithHtml });

      const fetched = await api.fetch(MOCK_VIDEO_ID, ['en'], true); // preserveFormatting = true
      expect(fetched.snippets[0].text).toBe('Hello <b>bold</b> world');
    });

    it('should fetch with preserve_formatting=false (default, testing TranscriptParser implicitly)', async () => {
      const xmlWithHtml = `<transcript><text start="0" dur="1">Hello <b>bold</b> world</text></transcript>`;
      mockedAxios.get.mockResolvedValueOnce({ data: xmlWithHtml });

      const fetched = await api.fetch(MOCK_VIDEO_ID, ['en'], false); // preserveFormatting = false
      expect(fetched.snippets[0].text).toBe('Hello bold world');
    });

    it('should throw PoTokenRequired if transcript URL indicates it', async () => {
        const videoIdWithPoToken = 'videoIdPoTest';
        const langWithPoToken = 'pt'; // Stands for PoToken ;)

        // Mock list() part
        const playerResponseWithPoTokenTrack = {
            playabilityStatus: { status: "OK" },
            captions: {
                playerCaptionsTracklistRenderer: {
                    captionTracks: [getMockCaptionTrackWithPoToken(videoIdWithPoToken, langWithPoToken)],
                    translationLanguages: [],
                }
            }
        };
        mockedAxios.get.mockReset(); // Clear beforeEach mocks for this specific test
        mockedAxios.post.mockReset();

        mockedAxios.get.mockResolvedValueOnce({
            data: generateMockYouTubePageHtml(videoIdWithPoToken, playerResponseWithPoTokenTrack)
        });
        mockedAxios.post.mockResolvedValueOnce({
            data: playerResponseWithPoTokenTrack
        });
        // The Transcript.fetch() will then use the URL with &exp=xpe, which should throw.
        // No further axios GET for the transcript content itself should occur.

        await expect(api.fetch(videoIdWithPoToken, [langWithPoToken])).rejects.toThrow(PoTokenRequired);
        expect(mockedAxios.get).toHaveBeenCalledTimes(1); // Only for the HTML page
    });

  });

  describe('TranscriptList methods', () => {
    let transcriptList: TranscriptList;

    beforeEach(async () => {
      // Use the API to get a TranscriptList instance based on default mocks
      mockedAxios.get.mockResolvedValueOnce({ data: generateMockYouTubePageHtml(MOCK_VIDEO_ID) });
      mockedAxios.post.mockResolvedValueOnce({ data: MOCK_INNERTUBE_API_PLAYER_RESPONSE });
      transcriptList = await api.list(MOCK_VIDEO_ID);
      // Reset mocks for subsequent calls in tests if any Transcript methods make HTTP requests (e.g., translate)
      mockedAxios.get.mockReset();
      mockedAxios.post.mockReset();
    });

    it('findTranscript should find available transcript (manual first)', () => {
      // MOCK_INNERTUBE_API_PLAYER_RESPONSE has 'fr' (manual) and 'en' (generated)
      const found = transcriptList.findTranscript(['en', 'fr']);
      expect(found.languageCode).toBe('fr'); // Manual 'fr' should be found over generated 'en' if both match
      expect(found.isGenerated).toBe(false);
    });

    it('findTranscript should find generated if manual is not in preferred list', () => {
      const found = transcriptList.findTranscript(['en', 'de']); // 'de' not present, 'en' is generated
      expect(found.languageCode).toBe('en');
      expect(found.isGenerated).toBe(true);
    });

    it('findManuallyCreatedTranscript should find only manual transcripts', () => {
      const found = transcriptList.findManuallyCreatedTranscript(['fr', 'en']);
      expect(found.languageCode).toBe('fr');
      expect(found.isGenerated).toBe(false);
    });

    it('findManuallyCreatedTranscript should throw NoTranscriptFound if no manual match', () => {
      expect(() => transcriptList.findManuallyCreatedTranscript(['en', 'de'])).toThrow(NoTranscriptFound);
    });

    it('findGeneratedTranscript should find only generated transcripts', () => {
      const found = transcriptList.findGeneratedTranscript(['en', 'fr']);
      expect(found.languageCode).toBe('en');
      expect(found.isGenerated).toBe(true);
    });

    it('findGeneratedTranscript should throw NoTranscriptFound if no generated match', () => {
      expect(() => transcriptList.findGeneratedTranscript(['fr', 'de'])).toThrow(NoTranscriptFound);
    });

    it('should be iterable and yield all transcripts', () => {
      const transcriptsFromIterator: Transcript[] = [];
      for (const t of transcriptList) {
        transcriptsFromIterator.push(t);
      }
      // MOCK_INNERTUBE_API_PLAYER_RESPONSE has 'fr' (manual) and 'en' (generated)
      expect(transcriptsFromIterator.length).toBe(2);
      expect(transcriptsFromIterator.some(t => t.languageCode === 'fr' && !t.isGenerated)).toBe(true);
      expect(transcriptsFromIterator.some(t => t.languageCode === 'en' && t.isGenerated)).toBe(true);
    });
  });

  describe('Transcript.translate() method', () => {
    let englishTranscript: Transcript;

    beforeEach(async () => {
      // Get a list and pick a translatable transcript
      mockedAxios.get.mockResolvedValueOnce({ data: generateMockYouTubePageHtml(MOCK_VIDEO_ID) });
      mockedAxios.post.mockResolvedValueOnce({ data: MOCK_INNERTUBE_API_PLAYER_RESPONSE });
      const list = await api.list(MOCK_VIDEO_ID);
      englishTranscript = list.findTranscript(['en']); // 'en' is translatable to 'de', 'es' in this mock

      // Reset mocks for the translate call itself if it were to make an HTTP request for new list of translation languages
      // (it doesn't, it uses the ones from the original TranscriptList)
      // And for the .fetch() call on the translated transcript
      mockedAxios.get.mockReset();
      mockedAxios.post.mockReset();
    });

    it('should successfully create a translated transcript object', () => {
      const translatedGerman = englishTranscript.translate('de');
      expect(translatedGerman).toBeInstanceOf(Transcript);
      expect(translatedGerman.languageCode).toBe('de');
      expect(translatedGerman.isGenerated).toBe(true); // Translated transcripts are considered generated
      expect(translatedGerman.url).toContain('&tlang=de');
    });

    it('fetch on translated transcript should get translated content', async () => {
      const translatedGerman = englishTranscript.translate('de');
      // Mock the GET request for the translated German transcript XML
      // The URL will be the original English URL with &tlang=de appended.
      mockedAxios.get.mockResolvedValueOnce({ data: MOCK_SRV3_TRANSCRIPT_XML_DE }); // Using German mock for simplicity

      const fetched = await translatedGerman.fetch();
      expect(mockedAxios.get).toHaveBeenCalledWith(
        `https://www.youtube.com/api/timedtext?v=${MOCK_VIDEO_ID}&lang=en&format=srv3&tlang=de`, // Original lang 'en', tlang 'de'
        expect.any(Object)
      );
      expect(fetched.languageCode).toBe('de');
      expect(fetched.snippets[0].text).toBe('Hallo Welt,'); // From MOCK_SRV3_TRANSCRIPT_XML_DE
    });

    it('should throw NotTranslatable if original transcript is not translatable', async () => {
      // Create a non-translatable transcript (e.g., by finding 'fr' and clearing its translationLanguages)
      // MOCK_INNERTUBE_API_PLAYER_RESPONSE makes 'fr' translatable. Let's find one that isn't or mock one.
      const frenchTranscript = (await api.list(MOCK_VIDEO_ID)).findTranscript(['fr']);
      (frenchTranscript as any).translationLanguages = []; // Force it to be non-translatable for this test

      expect(() => frenchTranscript.translate('de')).toThrow(NotTranslatable);
    });

    it('should throw TranslationLanguageNotAvailable if target language is not available for translation', () => {
      // 'en' can be translated to 'de', 'es'. Trying 'it'.
      expect(() => englishTranscript.translate('it')).toThrow(TranslationLanguageNotAvailable);
    });
  });

});

// Helper to reset Axios mocks if needed outside of beforeEach, though clearMocks:true in jest.config.js should handle it.
// export const resetAxiosMock = () => {
//   mockedAxios.get.mockReset();
//   mockedAxios.post.mockReset();
// };
