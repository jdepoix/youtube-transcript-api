FROM python:3

COPY . /app

WORKDIR /app

RUN python setup.py install

ENTRYPOINT ["youtube_transcript_api"]
