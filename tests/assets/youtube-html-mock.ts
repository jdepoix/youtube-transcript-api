// Simplified mock HTML for a YouTube video page
// This needs to contain the INNERTUBE_API_KEY and the player response object (or parts of it)
// that TranscriptListFetcher expects to parse.

export const MOCK_VIDEO_ID = 'testVideoId123';
export const MOCK_API_KEY = 'testApiKey-xxxxxxxxxxx';

export const generateMockYouTubePageHtml = (
  videoId: string,
  playerResponseOverride?: any, // Allow overriding the player_response for different test cases
  apiKeyOverride?: string
): string => {
  const apiKey = apiKeyOverride || MOCK_API_KEY;

  // A minimal player response structure that TranscriptListFetcher might look for.
  // This will be stringified and embedded in the HTML.
  // It needs `captions.playerCaptionsTracklistRenderer` for transcript listing.
  const defaultPlayerResponse = {
    playabilityStatus: {
      status: 'OK',
    },
    captions: {
      playerCaptionsTracklistRenderer: {
        captionTracks: [
          {
            baseUrl: `https://www.youtube.com/api/timedtext?v=${videoId}&lang=en&format=srv3`,
            name: { simpleText: 'English' }, // In actual response, it's {runs: [{text: 'English'}]}
            languageCode: 'en',
            kind: 'asr', // Auto Speech Recognition
            isTranslatable: true,
          },
          {
            baseUrl: `https://www.youtube.com/api/timedtext?v=${videoId}&lang=de&format=srv3`,
            name: { simpleText: 'German' },
            languageCode: 'de',
            isTranslatable: true,
          },
          {
            baseUrl: `https://www.youtube.com/api/timedtext?v=${videoId}&lang=es&format=srv3`,
            name: { simpleText: 'Spanish (Spain) - Manual' },
            languageCode: 'es',
            vssId: '.es', // Manually created often have specific vssId like .en, a.fr, etc.
            isTranslatable: true,
          }
        ],
        translationLanguages: [
          { languageCode: 'fr', languageName: { simpleText: 'French' } },
          { languageCode: 'it', languageName: { simpleText: 'Italian' } },
        ],
      },
    },
    // Other parts of player_response might be needed for different error condition tests
  };

  const playerResponseToEmbed = playerResponseOverride || defaultPlayerResponse;

  // Simulate the structure where player_response is embedded as JSON in a script tag
  // and INNERTUBE_API_KEY is also available.
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Mock YouTube Page</title>
    </head>
    <body>
      <script>
        var ytInitialPlayerResponse = ${JSON.stringify(playerResponseToEmbed)};
        // In actual YouTube HTML, this might be within a ytplayer.config object
        // For testing, placing it directly is simpler if TranscriptListFetcher can find it.
        // The current implementation of _extractInnertubeApiKey looks for "INNERTUBE_API_KEY":"..."
      </script>
      <script>
        // Another script tag or inline script where API key might be found
        var ytplayer = ytplayer || {};
        ytplayer.config = ytplayer.config || {};
        ytplayer.config.args = ytplayer.config.args || {};
        ytplayer.config.args.raw_player_response = ${JSON.stringify(playerResponseToEmbed)}; // Alternative location

        // Simulate INNERTUBE_API_KEY (this exact pattern is searched for)
        var someOtherVar = {"INNERTUBE_API_KEY":"${apiKey}"};

      </script>
      <div id="player"></div>
      <div class="g-recaptcha"></div> <!-- For testing IpBlocked -->
      <form action="https://consent.youtube.com/s"></form> <!-- For testing consent page -->
    </body>
    </html>
  `;
};

// Mock for player_response when transcripts are disabled
export const mockPlayerResponseTranscriptsDisabled = {
  playabilityStatus: {
    status: 'OK',
  },
  captions: {}, // No playerCaptionsTracklistRenderer
};

// Mock for player_response when video is unavailable
export const mockPlayerResponseVideoUnavailable = {
  playabilityStatus: {
    status: 'ERROR',
    reason: 'Video unavailable', // Matches PlayabilityFailedReason.VIDEO_UNAVAILABLE
  },
};

// Mock for player_response when video is unplayable (generic)
export const mockPlayerResponseVideoUnplayable = {
  playabilityStatus: {
    status: 'UNPLAYABLE', // Matches PlayabilityStatus.UNPLAYABLE
    reason: 'This video is unplayable.',
    errorScreen: {
      playerErrorMessageRenderer: {
        subreason: {
          runs: [{text: 'Some detailed reason here.'}]
        }
      }
    }
  },
};

// Mock for age-restricted video
export const mockPlayerResponseAgeRestricted = {
    playabilityStatus: {
        status: "LOGIN_REQUIRED",
        reason: "This video may be inappropriate for some users.", // PlayabilityFailedReason.AGE_RESTRICTED
        errorScreen: { /* ... */ }
    }
};

// Mock for consent page HTML (very basic)
export const MOCK_CONSENT_PAGE_HTML = `
  <html><body>
    <form action="https://consent.youtube.com/s" method="POST">
      <input type="hidden" name="v" value="test_consent_value">
      <button type="submit">I AGREE</button>
    </form>
  </body></html>
`;

// Mock for IP Blocked (recaptcha)
// The HTML structure for this is just the presence of 'class="g-recaptcha"'
// The _extractInnertubeApiKey method checks for this.
// So, generateMockYouTubePageHtml already includes this.
// We'd simulate this by having _extractInnertubeApiKey not find the API key
// and then find the recaptcha class.

// Mock for InnerTube API response (POST to /youtubei/v1/player)
// This is what _fetchInnertubeData would get.
// For most successful cases, the initial HTML page's player response is used.
// However, _fetchInnertubeData IS called. Its response often mirrors or refines initial player response.
// If the initial HTML doesn't have player_response, this becomes critical.
// For simplicity, we can assume _fetchInnertubeData returns a similar structure
// as defaultPlayerResponse if the test doesn't focus on discrepancies.

export const MOCK_INNERTUBE_API_PLAYER_RESPONSE = {
    playabilityStatus: { status: "OK" },
    captions: {
        playerCaptionsTracklistRenderer: {
            captionTracks: [
                {
                    baseUrl: `https://www.youtube.com/api/timedtext?v=${MOCK_VIDEO_ID}&lang=en&format=srv3`,
                    name: { runs: [{text: 'English (auto)'}] }, // More realistic 'runs' structure
                    languageCode: 'en',
                    kind: 'asr',
                    isTranslatable: true,
                },
                 {
                    baseUrl: `https://www.youtube.com/api/timedtext?v=${MOCK_VIDEO_ID}&lang=fr&format=srv3`,
                    name: { runs: [{text: 'French'}] },
                    languageCode: 'fr',
                    vssId: '.fr', // Manual
                    isTranslatable: true,
                }
            ],
            translationLanguages: [
                { languageCode: 'de', languageName: { runs: [{text: 'German'}] } },
                { languageCode: 'es', languageName: { runs: [{text: 'Spanish'}] } },
            ],
        }
    }
};

export const MOCK_INNERTUBE_API_PLAYER_RESPONSE_NO_CAPTIONS = {
    playabilityStatus: { status: "OK" },
    captions: {} // No captions data
};

export const MOCK_INNERTUBE_PLAYER_RESPONSE_AGE_RESTRICTED = {
    playabilityStatus: {
        status: "LOGIN_REQUIRED",
        reason: "This video may be inappropriate for some users.",
    }
};

// Add more specific mock player responses for different error types as needed
// e.g., VideoUnplayable, RequestBlocked (though this is often a network error or HTML response)

// Mock XML for transcript data (srv3 format)
export const MOCK_SRV3_TRANSCRIPT_XML_EN = `
<transcript>
  <text start="0.123" dur="1.456">Hello world,</text>
  <text start="1.579" dur="2.345">this is a test transcript.</text>
  <text start="3.924" dur="1.000">English version.</text>
</transcript>
`;

export const MOCK_SRV3_TRANSCRIPT_XML_DE = `
<transcript>
  <text start="0.200" dur="1.500">Hallo Welt,</text>
  <text start="1.700" dur="2.000">dies ist ein Testtranskript.</text>
  <text start="3.700" dur="1.200">Deutsche Version.</text>
</transcript>
`;

export const MOCK_SRV3_TRANSCRIPT_XML_FR_TRANSLATED = `
<transcript>
  <text start="0.123" dur="1.456">Bonjour le monde,</text>
  <text start="1.579" dur="2.345">ceci est une transcription de test.</text>
  <text start="3.924" dur="1.000">Version française.</text>
</transcript>
`;

// Mock for HTML when YouTube blocks with a "Too Many Requests" type page
export const MOCK_TOO_MANY_REQUESTS_HTML = `
<html><head><title>Too Many Requests</title></head><body>You have made too many requests recently.</body></html>
`;

// Mock for HTML when YouTube blocks with a "Unavailable For Legal Reasons" type page
export const MOCK_UNAVAILABLE_FOR_LEGAL_REASONS_HTML = `
<html><head><title>Unavailable</title></head><body>This video is unavailable in your country due to legal reasons.</body></html>
`;

// Mock for player_response when PoToken is required (simulated)
// This typically happens if the captionTrack URL itself contains "&exp=xpe"
// The error is raised by Transcript.fetch, not usually by TranscriptListFetcher directly.
// So, the caption track URL in generateMockYouTubePageHtml or MOCK_INNERTUBE_API_PLAYER_RESPONSE
// would need to include this parameter for a PoTokenRequired test.
export const getMockCaptionTrackWithPoToken = (videoId: string, lang: string) => ({
    baseUrl: `https://www.youtube.com/api/timedtext?v=${videoId}&lang=${lang}&format=srv3&exp=xpe&token=mocktoken`,
    name: { simpleText: lang === 'en' ? 'English' : 'Other' },
    languageCode: lang,
    isTranslatable: true,
});

// HTML page that does not contain INNERTUBE_API_KEY
export const MOCK_HTML_NO_API_KEY = `
<!DOCTYPE html>
<html><body>No API Key Here</body></html>
`;

// HTML page that does not contain ytInitialPlayerResponse
export const MOCK_HTML_NO_PLAYER_RESPONSE = `
<!DOCTYPE html>
<html><body>
 <script>
    // Simulate INNERTUBE_API_KEY (this exact pattern is searched for)
    var someOtherVar = {"INNERTUBE_API_KEY":"${MOCK_API_KEY}"};
  </script>
</body></html>
`;

// Innertube response for a video that is members-only
export const MOCK_INNERTUBE_MEMBERS_ONLY = {
  playabilityStatus: {
    status: "LOGIN_REQUIRED", // Or sometimes "UNPLAYABLE" with a specific reason
    reason: "This video is available to channel members only.",
    errorScreen: {
      playerErrorMessageRenderer: {
        subreason: {
          runs: [{ text: "This video is available to channel members on level: Member (or higher)." }]
        }
      }
    }
  },
  // No captions object or it's empty
  captions: {},
};

// Innertube response for a video that is private
export const MOCK_INNERTUBE_PRIVATE_VIDEO = {
  playabilityStatus: {
    status: "ERROR", // Or sometimes "UNPLAYABLE"
    reason: "This video is private.",
     errorScreen: {
      playerErrorMessageRenderer: {
        subreason: {
          runs: [{ text: "This is a private video. Please sign in to verify that you may see it." }]
        }
      }
    }
  },
  captions: {},
};
