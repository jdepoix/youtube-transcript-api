from youtube_transcript_api import YouTubeTranscriptApi

video_id = 'qGVLqLxAl0I'   # this is a video ID from Youtube about Nitric Oxide for example
			   # the output is written to a text file, my future code will automatically pull the title of the video
			   # but that will require use of some Google API and will be optional

# my python based on youtube-transcript-api, 
# it's a python script to pull the transcription, 
# but the output is to a text file and has pseudo 
# paragraphs and lines of 15 words to make it more readable. 
# also, my transcript pull is void of time indexes.

# I tend to read faster than the Youtube can play video wise. 
# And I retain the content better when I read. 
# And this is why I took the approach below.

try:
    # Fetching the transcript
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    # Extracting words and flattening the list of words
    words = [word for segment in transcript for word in segment['text'].split()]

    # Variables to keep track of lines and paragraphs
    line_count, paragraph_count = 0, 0
    line_length = 15  # 15 words per line
    paragraph_length = 6  # 6 lines per paragraph

    # Opening the file to write
    # this example I've altered the default of the text file name. My intention is to have the name of the text file 
    # have the name of the video in it's title to avoid duplicate file names. 

    with open('NO2_formatted_transcript.txt', 'w') as file:
        for index, word in enumerate(words):
            # Writing the word to the file
            file.write(word + ' ')

            # Check if a line is completed
            if (index + 1) % line_length == 0:
                file.write('\n')
                line_count += 1

                # Check if a paragraph is completed
                if line_count % paragraph_length == 0:
                    file.write('\n\n')  # Adding an extra newline for a new paragraph

    print("Transcript words have been saved to transcript_words.txt")

except Exception as e:
    print(f"An error occurred: {e}")

