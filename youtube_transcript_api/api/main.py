
from fastapi import FastAPI, Query
from youtube_transcript_api import YouTubeTranscriptApi
from proxy_config_local import PROXIES
from fastapi.responses import JSONResponse

app = FastAPI()

LANGUAGES = ["pt-BR", "pt", "en-US"]

@app.get("/transcribe")
def transcribe(video_id: str = Query(..., description="YouTube video ID")):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=LANGUAGES, proxies=PROXIES
        )
        return {"video_id": video_id, "lines": transcript}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e), "video_id": video_id}
        )
