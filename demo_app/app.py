from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_file, session, url_for

from yt_history_inspector import HistoryInspector
from yt_history_inspector.wordclouds import render_wordcloud


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("YTHI_FLASK_SECRET", "dev-secret")

    base_dir = Path(os.environ.get("YTHI_DATA_DIR", "data"))
    base_dir.mkdir(parents=True, exist_ok=True)

    db_path = os.environ.get("YTHI_DB_PATH", str(base_dir / "app.db"))
    client_secret = os.environ.get("YTHI_CLIENT_SECRET", "client_secret.json")
    history_playlist_id = os.environ.get("YTHI_HISTORY_PLAYLIST_ID", "HL")

    inspector = HistoryInspector(
        db_path=db_path,
        client_secrets_path=client_secret,
        history_playlist_id=history_playlist_id,
    )

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/auth/start")
    def auth_start():
        redirect_uri = _redirect_uri()
        url, state = inspector.get_authorization_url(redirect_uri)
        session["oauth_state"] = state
        return redirect(url)

    @app.route("/auth/callback")
    def auth_callback():
        code = request.args.get("code")
        if not code:
            return render_template("index.html", error="OAuth code missing.")
        token_json = inspector.exchange_code(_redirect_uri(), code)
        inspector.save_credentials(token_json)
        return redirect(url_for("timeline"))

    @app.route("/sync")
    def sync():
        result = inspector.sync_history(max_items=200)
        transcript_result = inspector.sync_transcripts_for_visible(limit=200)
        return render_template(
            "sync.html",
            result=result,
            transcript_result=transcript_result,
        )

    @app.route("/transcript/<video_id>", methods=["POST"])
    def get_transcript(video_id: str):
        inspector.sync_transcripts([video_id])
        inspector.process_transcript_queue(limit=1)
        return redirect(request.referrer or url_for("timeline"))


    @app.route("/timeline")
    def timeline():
        page = max(int(request.args.get("page", 1)), 1)
        per_page = max(min(int(request.args.get("per_page", 50)), 200), 10)
        include_hidden = request.args.get("include_hidden") == "1"
        no_transcript = request.args.get("no_transcript") == "1"
        data = inspector.timeline(
            page=page,
            per_page=per_page,
            include_hidden=include_hidden,
            no_transcript=no_transcript,
        )
        return render_template(
            "timeline.html",
            timeline=data["items"],
            page=data["page"],
            per_page=data["per_page"],
            total=data["total"],
            has_prev=data["has_prev"],
            has_next=data["has_next"],
            include_hidden=include_hidden,
            no_transcript=no_transcript,
        )

    @app.route("/video/<video_id>")
    def video_detail(video_id: str):
        data = inspector.video_detail(video_id)
        if not data:
            return render_template("timeline.html", timeline=[], error="Video not found.")
        return render_template("video.html", video=data)

    @app.route("/hide/<video_id>", methods=["POST"])
    def hide(video_id: str):
        reason = request.form.get("reason") or "manual"
        inspector.hide_video(video_id, reason=reason)
        return redirect(request.referrer or url_for("timeline"))

    @app.route("/show/<video_id>", methods=["POST"])
    def show(video_id: str):
        inspector.show_video(video_id)
        return redirect(request.referrer or url_for("timeline"))

    @app.route("/wordcloud.png")
    def wordcloud():
        counts = inspector.wordcloud_counts(limit=300)
        cloud = render_wordcloud(counts)
        output_path = base_dir / "wordcloud.png"
        cloud.to_file(str(output_path))
        return send_file(output_path, mimetype="image/png")

    return app


def _redirect_uri() -> str:
    base_url = os.environ.get("YTHI_BASE_URL", "http://localhost:8080")
    return f"{base_url}/auth/callback"


def _detect_takeout_files(uploaded_path: Path, base_dir: Path) -> list[Path]:
    suffixes = [s.lower() for s in uploaded_path.suffixes]
    if uploaded_path.suffix.lower() in {".json", ".csv", ".html"}:
        return [uploaded_path]
    extract_root = base_dir / "takeout_uploads" / datetime.utcnow().strftime("%Y%m%d%H%M%S")
    extract_root.mkdir(parents=True, exist_ok=True)
    if uploaded_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(uploaded_path, "r") as handle:
            handle.extractall(extract_root)
    elif suffixes[-2:] == [".tar", ".gz"] or uploaded_path.suffix.lower() == ".tgz":
        with tarfile.open(uploaded_path, "r:gz") as handle:
            handle.extractall(extract_root)
    else:
        return []
    return [extract_root]


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
