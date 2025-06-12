export const WATCH_URL = 'https://www.youtube.com/watch?v={video_id}';

export const INNERTUBE_API_URL = 'https://www.youtube.com/youtubei/v1/player?key={api_key}';

export const INNERTUBE_CONTEXT = {
  client: {
    clientName: 'WEB',
    clientVersion: '2.20210721.00.00', // This might need to be updated periodically
    hl: 'en',
    gl: 'US',
    utcOffsetMinutes: 0,
  },
  user: {},
  request: {},
};
