export class YouTubeTranscriptApiException extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class CookieError extends YouTubeTranscriptApiException {}

export class CookiePathInvalid extends CookieError {
  constructor(cookiePath: string) {
    super(`Can't load the provided cookie file: ${cookiePath}`);
  }
}

export class CookieInvalid extends CookieError {
  constructor(cookiePath: string) {
    super(`The cookies provided are not valid (may have expired): ${cookiePath}`);
  }
}

export class CouldNotRetrieveTranscript extends YouTubeTranscriptApiException {
  videoId: string;
  causeMessage = "";

  constructor(videoId: string, message?: string) {
    super(message || `Could not retrieve a transcript for the video ${videoId}!`);
    this.videoId = videoId;
  }

  protected getCauseMessage(): string {
    return this.causeMessage;
  }

  toString(): string {
    let errorMessage = super.toString();
    const cause = this.getCauseMessage();
    if (cause) {
      errorMessage += `\nThis is most likely caused by:\n\n${cause}`;
      errorMessage += `\n\nIf you are sure that the described cause is not responsible for this error and that a transcript should be retrievable, please create an issue at https://github.com/jdepoix/youtube-transcript-api/issues. Please add which version of youtube_transcript_api you are using and provide the information needed to replicate the error. Also make sure that there are no open issues which already describe your problem!`;
    }
    return errorMessage;
  }
}

export class YouTubeDataUnparsable extends CouldNotRetrieveTranscript {
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = "The data required to fetch the transcript is not parsable. This should not happen, please open an issue (make sure to include the video ID)!";
  }
}

export class YouTubeRequestFailed extends CouldNotRetrieveTranscript {
  reason: string;

  constructor(videoId: string, httpError: Error) { // Assuming httpError is of type Error for simplicity
    super(videoId);
    this.reason = httpError.message;
    this.causeMessage = `Request to YouTube failed: ${this.reason}`;
  }
}

export class VideoUnplayable extends CouldNotRetrieveTranscript {
  reason?: string;
  subReasons: string[];

  constructor(videoId: string, reason?: string, subReasons: string[] = []) {
    super(videoId);
    this.reason = reason;
    this.subReasons = subReasons;
  }

  protected getCauseMessage(): string {
    let cause = "The video is unplayable for the following reason: ";
    cause += this.reason || "No reason specified!";
    if (this.subReasons.length > 0) {
      cause += "\n\nAdditional Details:\n";
      cause += this.subReasons.map(subReason => ` - ${subReason}`).join("\n");
    }
    return cause;
  }
}

export class VideoUnavailable extends CouldNotRetrieveTranscript {
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = "The video is no longer available";
  }
}

export class InvalidVideoId extends CouldNotRetrieveTranscript {
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = 'You provided an invalid video id. Make sure you are using the video id and NOT the url!\n\nDo NOT run: `YouTubeTranscriptApi.getTranscript("https://www.youtube.com/watch?v=1234")`\nInstead run: `YouTubeTranscriptApi.getTranscript("1234")`';
  }
}

export class RequestBlocked extends CouldNotRetrieveTranscript {
  // Further customization for proxyConfig can be added if needed
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = `YouTube is blocking requests from your IP. This usually is due to one of the following reasons:\n- You have done too many requests and your IP has been blocked by YouTube\n- You are doing requests from an IP belonging to a cloud provider (like AWS, Google Cloud Platform, Azure, etc.). Unfortunately, most IPs from cloud providers are blocked by YouTube.\n\nThere are two things you can do to work around this:\n1. Use proxies to hide your IP address, as explained in the "Working around IP bans" section of the README (https://github.com/jdepoix/youtube-transcript-api?tab=readme-ov-file#working-around-ip-bans-requestblocked-or-ipblocked-exception).\n2. (NOT RECOMMENDED) If you authenticate your requests using cookies, you will be able to continue doing requests for a while. However, YouTube will eventually permanently ban the account that you have used to authenticate with! So only do this if you don't mind your account being banned!`;
  }

  // In a real scenario, you might pass proxyConfig and adjust the message
  // For now, using the generic message.
}

export class IpBlocked extends RequestBlocked {
    constructor(videoId: string) {
        super(videoId);
        this.causeMessage = `YouTube is blocking requests from your IP. This usually is due to one of the following reasons:\n- You have done too many requests and your IP has been blocked by YouTube\n- You are doing requests from an IP belonging to a cloud provider (like AWS, Google Cloud Platform, Azure, etc.). Unfortunately, most IPs from cloud providers are blocked by YouTube.\n\nWays to work around this are explained in the "Working around IP bans" section of the README (https://github.com/jdepoix/youtube-transcript-api?tab=readme-ov-file#working-around-ip-bans-requestblocked-or-ipblocked-exception).\n`;
    }
}


export class TranscriptsDisabled extends CouldNotRetrieveTranscript {
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = "Subtitles are disabled for this video";
  }
}

export class AgeRestricted extends CouldNotRetrieveTranscript {
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = "This video is age-restricted. Therefore, you are unable to retrieve transcripts for it without authenticating yourself.\n\nUnfortunately, Cookie Authentication is temporarily unsupported in youtube-transcript-api, as recent changes in YouTube's API broke the previous implementation. I will do my best to re-implement it as soon as possible.";
  }
}

export class NotTranslatable extends CouldNotRetrieveTranscript {
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = "The requested language is not translatable";
  }
}

export class TranslationLanguageNotAvailable extends CouldNotRetrieveTranscript {
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = "The requested translation language is not available";
  }
}

export class FailedToCreateConsentCookie extends CouldNotRetrieveTranscript {
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = "Failed to automatically give consent to saving cookies";
  }
}

export class NoTranscriptFound extends CouldNotRetrieveTranscript {
  constructor(videoId: string, requestedLanguageCodes: string[], transcriptData: any /* TranscriptList */) {
    super(videoId);
    // In a real scenario, TranscriptList would be a defined type/interface
    this.causeMessage = `No transcripts were found for any of the requested language codes: ${requestedLanguageCodes.join(', ')}\n\n${JSON.stringify(transcriptData, null, 2)}`;
  }
}

export class PoTokenRequired extends CouldNotRetrieveTranscript {
  constructor(videoId: string) {
    super(videoId);
    this.causeMessage = "The requested video cannot be retrieved without a PO Token. If this happens, please open a GitHub issue!";
  }
}
