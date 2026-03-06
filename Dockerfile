FROM python:3.12-slim

WORKDIR /app

# Install build deps and Python deps before copying app code for better layer caching.
COPY requirements-demo.txt /app/
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && pip install --no-cache-dir -r requirements-demo.txt \
    && apt-get purge -y --auto-remove gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock README.md /app/
COPY youtube_transcript_api /app/youtube_transcript_api
COPY yt_history_inspector /app/yt_history_inspector
COPY demo_app /app/demo_app

RUN touch /app/client_secret.json \
    && pip install --no-cache-dir .

EXPOSE 8080

CMD ["python", "-m", "demo_app.app"]
