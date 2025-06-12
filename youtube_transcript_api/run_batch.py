
import json
from youtube_transcript_api import YouTubeTranscriptApi
from proxy_config_local import PROXIES

VIDEO_IDS = [
    "iF80mLGqv0Y", "SyeWu4V6GJ8", "4h6hOdEdPJQ", "TnqopIImhd0", "1JjgZ47YsBE",
    "H5nyh9hffl4", "HFJvXWO-QmU", "wgOTQuS4JPk", "4r55eIvIyEM", "-hntgh7J4ho", "y751QH1SHXU"
]

LANGUAGES = ["pt-BR", "pt", "en-US", "en", "es"]

def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=LANGUAGES, proxies=PROXIES)
        return transcript
    except Exception as e:
        return str(e)

def main():
    results = {}

    for video_id in VIDEO_IDS:
        print(f"🎬 Buscando transcrição para: {video_id}")
        result = fetch_transcript(video_id)

        if isinstance(result, list):
            print(f"✅ Transcrição OK ({len(result)} blocos)")
            results[video_id] = {
                "status": "ok",
                "lines": result[:5]  # Exibir só primeiras 5 linhas
            }
        else:
            print(f"❌ Falha: {result}")
            results[video_id] = {
                "status": "erro",
                "mensagem": result
            }

    with open("batch_transcripts_summary.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n📝 Resumo salvo em batch_transcripts_summary.json")

if __name__ == "__main__":
    main()
