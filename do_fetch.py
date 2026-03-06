
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi

# video_id = "OBM7R3Qo9Bs"

#video_id = "2JiMmye2ezg"
video_id = "JYcidOS9ozU"


ytt_api = YouTubeTranscriptApi()
fetched_transcript = ytt_api.fetch(video_id, languages=['en'])

# collect full text
full_text = "\n".join(snippet.text for snippet in fetched_transcript)

print(full_text)
print(f"\n--- {len(fetched_transcript)} snippets ---")

# copy to macOS clipboard
process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
process.communicate(full_text.encode('utf-8'))
print("Transcript copied to clipboard.")
