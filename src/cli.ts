#!/usr/bin/env node
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import fs from 'fs';
import { YouTubeTranscriptApi } from './youtube-transcript-api';
import { FormatterLoader, UnknownFormatterType } from './formatters';
import { ProxyConfig } from './proxies';
import { FetchedTranscript } from './types';
import { TranscriptList } from './transcript-list-fetcher'; // Assuming TranscriptList class is here

interface CliArgs {
  videoIds: string[];
  listTranscripts?: boolean;
  languages?: string[];
  excludeGenerated?: boolean;
  excludeManuallyCreated?: boolean;
  format?: string;
  translate?: string;
  webshareProxyUsername?: string;
  webshareProxyPassword?: string;
  httpProxy?: string;
  httpsProxy?: string;
  outputFile?: string;
  // For yargs, we use _ for array args and camelCase for options
  [key: string]: unknown; // Index signature for yargs
}

async function main() {
  const yargsInstance = yargs(hideBin(process.argv));
  const argv = await yargsInstance
    .usage('Usage: $0 <video_ids...> [options]')
    .option('list-transcripts', {
      alias: 'l',
      type: 'boolean',
      description: 'List available transcripts for the given videos.',
      default: false,
    })
    .option('video-ids', { // Explicitly define video-ids to handle it better
        type: 'string',
        demandOption: true, // Make it required, yargs will handle it from positional args
        description: 'One or more YouTube video IDs.',
        array: true, // Treat as an array even if one is passed
    })
    .option('languages', {
      alias: 'lang',
      type: 'array',
      string: true,
      description: 'List of language codes in descending priority (e.g., en de es).',
      default: ['en'],
    })
    .option('exclude-generated', {
      type: 'boolean',
      description: 'Exclude automatically generated transcripts.',
      default: false,
    })
    .option('exclude-manually-created', {
      type: 'boolean',
      description: 'Exclude manually created transcripts.',
      default: false,
    })
    .option('format', {
      type: 'string',
      description: 'Output format for transcripts.',
      choices: Object.keys(FormatterLoader.TYPES),
      default: 'pretty',
    })
    .option('translate', {
      alias: 't',
      type: 'string',
      description: 'Language code to translate the transcript to.',
    })
    .option('webshare-proxy-username', {
      type: 'string',
      description: 'Webshare proxy username (host/port must also be set via httpProxy/httpsProxy).',
    })
    .option('webshare-proxy-password', {
      type: 'string',
      description: 'Webshare proxy password.',
    })
    .option('http-proxy', {
      type: 'string',
      description: 'HTTP proxy URL (e.g., http://host:port or http://user:pass@host:port).',
    })
    .option('https-proxy', { // In axios, one proxy typically covers both, or use HTTPS_PROXY env var.
                            // For simplicity, we'll use httpProxy for both if httpsProxy is not set.
      type: 'string',
      description: 'HTTPS proxy URL (e.g., http://host:port or http://user:pass@host:port).',
    })
    .option('output-file', {
        alias: 'o',
        type: 'string',
        description: 'File to write the output to. If not set, prints to console.',
    })
    .help()
    .alias('help', 'h')
    .parseAsync();

  // Yargs puts positional arguments into '_' array by default.
  // If 'video-ids' option is used to capture them, it should be correct.
  // Let's ensure videoIds are correctly populated.
  const videoIds = (argv.videoIds || argv._.slice(0) as string[]).filter(v => typeof v === 'string');

  if (videoIds.length === 0) {
    console.error("Error: No video IDs provided.");
    yargsInstance.showHelp();
    process.exit(1);
  }


  if (argv.excludeManuallyCreated && argv.excludeGenerated) {
    console.log(''); // Mimic python version behavior
    process.exit(0);
  }

  let proxyConfig: ProxyConfig | undefined = undefined;

  if (argv.httpProxy || argv.httpsProxy) {
    // Axios typically uses a single proxy URL. If both httpProxy and httpsProxy are given,
    // httpsProxy is often preferred for https requests.
    // Our ProxyConfig takes a single host/port. We'll need to parse the URL.
    // For simplicity, if httpProxy is set, use it. User should ensure it matches their proxy's capability.
    const proxyUrlString = argv.httpProxy || argv.httpsProxy;
    if (proxyUrlString) {
        try {
            const url = new URL(proxyUrlString);
            proxyConfig = {
                host: url.hostname,
                port: parseInt(url.port, 10),
                protocol: url.protocol.replace(':', ''),
            };
            if (url.username || argv.webshareProxyUsername) { // Prioritize webshare specific if provided
                proxyConfig.auth = {
                    username: argv.webshareProxyUsername || url.username,
                    password: argv.webshareProxyPassword || url.password,
                };
            }
        } catch (e) {
            console.error(`Error: Invalid proxy URL provided: ${proxyUrlString}`);
            process.exit(1);
        }
    }
  } else if (argv.webshareProxyUsername && argv.webshareProxyPassword) {
      // This case is if only webshare credentials are provided without a full httpProxy URL
      // This implies a default host/port for webshare, which is not explicitly in our generic ProxyConfig
      // The Python CLI's WebshareProxyConfig had defaults. We'll require httpProxy for host/port.
      console.error("Error: Webshare username/password provided, but --http-proxy (with host and port) is missing.");
      process.exit(1);
  }


  const yttApi = new YouTubeTranscriptApi(proxyConfig);
  const fetchedItems: Array<FetchedTranscript | TranscriptList> = [];
  const exceptions: Error[] = [];

  for (const videoId of videoIds) {
    try {
      const transcriptList = await yttApi.list(videoId);
      if (argv.listTranscripts) {
        fetchedItems.push(transcriptList);
      } else {
        let transcriptToFetch;
        if (argv.excludeManuallyCreated) {
          transcriptToFetch = transcriptList.findGeneratedTranscript(argv.languages!);
        } else if (argv.excludeGenerated) {
          transcriptToFetch = transcriptList.findManuallyCreatedTranscript(argv.languages!);
        } else {
          transcriptToFetch = transcriptList.findTranscript(argv.languages!);
        }

        if (argv.translate) {
          transcriptToFetch = transcriptToFetch.translate(argv.translate);
        }
        // The fetch method on Transcript now returns FetchedTranscript
        const fetched = await transcriptToFetch.fetch(); // Assuming default preserveFormatting
        fetchedItems.push(fetched);
      }
    } catch (error: any) { {
      exceptions.push(error instanceof Error ? error : new Error(String(error)));
    }}
  }

  let outputString = "";
  const errorMessages = exceptions.map(e => e.message).join('\n\n');

  if (fetchedItems.length > 0) {
    if (argv.listTranscripts) {
      outputString = fetchedItems.map(item => (item as TranscriptList).toString()).join('\n\n');
    } else {
      try {
        const formatter = new FormatterLoader().load(argv.format);
        // Ensure all items are FetchedTranscript for formatTranscripts
        if (fetchedItems.every(item => 'snippets' in item)) {
            outputString = formatter.formatTranscripts(fetchedItems as FetchedTranscript[]);
        } else {
             // Should not happen if listTranscripts is false
            exceptions.push(new Error("Mixed item types found for formatting; expected only fetched transcripts."));
        }
      } catch (e: any) {
        exceptions.push(e instanceof Error ? e : new Error(String(e)));
      }
    }
  }

  const finalOutput = [outputString, errorMessages].filter(s => s).join('\n\n');

  if (argv.outputFile) {
    try {
      fs.writeFileSync(argv.outputFile, finalOutput);
      console.log(`Output successfully written to ${argv.outputFile}`);
    } catch (error: any) {
      console.error(`Error writing to file ${argv.outputFile}: ${error.message}`);
      // Optionally print to console if file write fails
      // console.log('\n' + finalOutput);
      process.exit(1);
    }
  } else {
    console.log(finalOutput);
  }

  if (exceptions.length > 0 && !argv.outputFile) {
    // If there were errors and not writing to a file, ensure a non-zero exit code if only errors were printed.
    // If there was some successful output along with errors, it might still be a 0 exit.
    // The Python CLI seems to print errors but doesn't explicitly exit with error code here.
    // For now, we'll just print. A more robust CLI might exit with error code if any exception occurred.
  }
}

main().catch(error => {
  console.error('An unexpected error occurred:');
  if (error instanceof Error) {
    console.error(error.message);
    if (error.stack) console.error(error.stack);
  } else {
    console.error(error);
  }
  process.exit(1);
});
