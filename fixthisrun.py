from selenium import webdriver
from selenium.webdriver.common.by import By

# URL of the YouTube video
url = 'https://www.youtube.com/watch?v=videoID'

# Set up the WebDriver (this example uses Chrome)
driver = webdriver.Chrome()

try:
    # Open the YouTube page
    driver.get(url)
    # Wait for the title to load and get its text
    # This is a simplistic approach; in a real-world scenario, you might need to add explicit waits.
    title_element = driver.find_element(By.CSS_SELECTOR, 'h1.title yt-formatted-string')
    title = title_element.text

    print(f"Video Title: {title}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Always remember to close the driver
    driver.quit()


# currently the Selenium install causes errors in this version


from youtube_transcript_api import YouTubeTranscriptApi


video_id = 'qGVLqLxAl0I'

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

