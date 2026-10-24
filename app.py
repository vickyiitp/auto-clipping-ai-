"""
=============================================================================
  AutoClip Studio — Modern Web Interface for YouTube Shorts Auto-Clipping
=============================================================================
"""

import os
import sys

# Ensure UTF-8 output encoding on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import time
import json
import uuid
import queue
import threading
import zipfile
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, send_file, send_from_directory

from main import (
    Config,
    SUBTITLE_PRESETS,
    GENRE_THEMES,
    GOOGLE_FONTS_CATALOG,
    detect_hardware_encoder,
    process_video_pipeline,
    inspect_youtube_video,
    inspect_local_video,
    get_system_memory_info,
    purge_temp_cache,
)

app = Flask(__name__, template_folder="templates", static_folder="static")

# In-memory storage for generation jobs
JOBS = {}

class GenerationJob:
    def __init__(self, job_id, params):
        self.job_id = job_id
        self.params = params
        self.status = "queued"  # queued, running, completed, failed
        self.progress = 5
        self.logs = []
        self.results = []
        self.error = None
        self.log_queue = queue.Queue()
        self.created_at = time.time()

    def add_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        self.log_queue.put(log_entry)

        # Estimate progress based on keywords
        msg = message.lower()
        if "downloading:" in msg and "%" in msg:
            try:
                import re
                pct_match = re.search(r"downloading:\s*([\d\.]+)%", msg)
                if pct_match:
                    dl_pct = float(pct_match.group(1))
                    # Smoothly advance progress from 5% to 25% during Step 1 download
                    self.progress = max(self.progress, min(25, int(5 + (dl_pct / 100.0) * 20)))
            except Exception:
                pass
        elif "download complete" in msg or "skipping download" in msg or "cached video" in msg or "using local uploaded video" in msg:
            self.progress = max(self.progress, 25)
        elif "step 1" in msg or "downloading" in msg:
            self.progress = max(self.progress, 8)
        elif "step 2" in msg or "extracting audio" in msg:
            self.progress = max(self.progress, 32)
        elif "step 3" in msg or "transcribing" in msg:
            self.progress = max(self.progress, 52)
        elif "step 4" in msg or "dividing into clips" in msg or "clip selection" in msg:
            self.progress = max(self.progress, 68)
        elif "step 5" in msg or "rendering" in msg or "encoding" in msg or "processing" in msg:
            self.progress = max(self.progress, 85)
        elif "pipeline complete" in msg or "confirmed box" in msg or "finished:" in msg or "finished successfully" in msg:
            self.progress = 100


def run_job_thread(job: GenerationJob):
    job.status = "running"
    source_label = job.params.get("local_video_path") or job.params.get("youtube_url")
    job.add_log(f"Starting pipeline for: {source_label}")
    try:
        results = process_video_pipeline(
            youtube_url=job.params.get("youtube_url"),
            local_video_path=job.params.get("local_video_path"),
            genre=job.params.get("genre", "Podcast"),
            num_clips=job.params.get("num_clips", Config.NUM_CLIPS),
            clip_min_sec=job.params.get("clip_min_sec", Config.CLIP_MIN_SEC),
            clip_max_sec=job.params.get("clip_max_sec", Config.CLIP_MAX_SEC),
            clipping_mode=job.params.get("clipping_mode", "smart_highlights"),
            chunk_size_sec=float(job.params.get("chunk_size_sec", 30.0)),
            sub_preset=job.params.get("sub_preset", "tiktok_yellow"),
            custom_sub_font=job.params.get("custom_sub_font"),
            custom_sub_size=job.params.get("custom_sub_size"),
            custom_words_per_line=job.params.get("custom_words_per_line"),
            custom_uppercase=job.params.get("custom_uppercase", True),
            sub_position=job.params.get("sub_position", "bottom"),
            highlight_words=job.params.get("highlight_words", True),
            resource_mode=job.params.get("resource_mode", "balanced"),
            download_resolution=job.params.get("download_resolution", "720p"),
            sub_language_mode=job.params.get("sub_language_mode", "en_translate"),
            log_callback=job.add_log,
        )
        job.results = results
        job.status = "completed"
        job.progress = 100
        job.add_log(f"Job finished successfully! Generated {len(results)} short(s).")
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.add_log(f"❌ Error during processing: {e}")
    finally:
        # Signal queue end
        job.log_queue.put(None)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/system_status")
def system_status():
    """Returns current live RAM, CPU %, and temp folder cache size."""
    mem_info = get_system_memory_info()
    temp_bytes = sum(f.stat().st_size for f in Config.TEMP_DIR.glob("*") if f.is_file()) if Config.TEMP_DIR.exists() else 0
    temp_mb = round(temp_bytes / (1024 * 1024), 1)
    return jsonify({
        "memory": mem_info,
        "temp_cache_mb": temp_mb,
    })


@app.route("/api/cleanup", methods=["POST"])
def cleanup_temp_cache():
    """Purges intermediate working files and forces garbage collection to free RAM & SSD space."""
    res = purge_temp_cache()
    return jsonify({
        "success": True,
        "freed_mb": res.get("freed_mb", 0),
        "deleted_files": res.get("deleted_files", 0),
    })


@app.route("/api/inspect", methods=["POST"])
def inspect_video():
    """Inspect YouTube video metadata without downloading (title, duration, recommended boxes)."""
    data = request.json or {}
    url = data.get("youtube_url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    info = inspect_youtube_video(url)
    return jsonify(info)


@app.route("/api/upload", methods=["POST"])
def upload_video():
    """Uploads a local video file from user's computer, inspects metadata and returns video info."""
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    file = request.files["video"]
    if not file or file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    ext = Path(file.filename).suffix.lower()
    allowed_exts = [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"]
    if ext not in allowed_exts:
        return jsonify({"error": f"Unsupported format '{ext}'. Allowed: {', '.join(allowed_exts)}"}), 400

    Config.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^\w\s-]", "", Path(file.filename).stem).strip().replace(" ", "_")
    safe_name = f"upload_{safe_stem[:35]}_{uuid.uuid4().hex[:6]}{ext}"
    save_path = Config.DOWNLOADS_DIR / safe_name
    file.save(str(save_path))

    meta = inspect_local_video(save_path)
    return jsonify(meta)


@app.route("/api/thumb/<path:filename>")
def serve_thumbnail(filename):
    """Serves generated thumbnail previews from temp directory."""
    return send_from_directory(str(Config.TEMP_DIR), filename)


@app.route("/api/presets")
def get_presets():
    fonts = [
        {"id": "Impact", "name": "Impact (Viral Shorts Standard)"},
        {"id": "Arial Black", "name": "Arial Black (Bold Heavy)"},
        {"id": "Trebuchet MS", "name": "Trebuchet MS (Clean Punchy)"},
        {"id": "Verdana", "name": "Verdana (Legible High Contrast)"},
        {"id": "Arial", "name": "Arial (Simple Neutral)"},
    ]

    sample_videos = [
        {
            "title": "Guru Randhawa - 'AZUL' MV (Singing Video)",
            "url": "https://youtu.be/vB0V3iCSzQw?si=j9OpIq5WWXHcEG-o",
            "tag": "Music Video / Singing",
            "recommended_preset": "neon_cyber",
        },
        {
            "title": "Me at the zoo (Fast 19s Test)",
            "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            "tag": "Quick Benchmark",
            "recommended_preset": "tiktok_yellow",
        },
    ]

    return jsonify({
        "presets": SUBTITLE_PRESETS,
        "genres": list(GENRE_THEMES.keys()),
        "genre_themes": GENRE_THEMES,
        "fonts": fonts,
        "hardware_encoder": detect_hardware_encoder(),
        "sample_videos": sample_videos,
        "default_config": {
            "genre": Config.GENRE,
            "num_clips": Config.NUM_CLIPS,
            "clip_min_sec": Config.CLIP_MIN_SEC,
            "clip_max_sec": Config.CLIP_MAX_SEC,
            "sub_preset": "tiktok_yellow",
            "words_per_line": Config.SUB_WORDS_PER_LINE,
        }
    })


@app.route("/api/videos")
def get_videos():
    """List all generated videos in output folder."""
    out_dir = Config.OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    video_files = []
    for f in sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = f.stat()
        video_files.append({
            "filename": f.name,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
            "url": f"/api/video/{f.name}",
            "download_url": f"/api/download/{f.name}",
        })
    return jsonify({"videos": video_files})


@app.route("/api/video/<filename>")
def stream_video(filename):
    """Serve video file with range request support for smooth playback."""
    file_path = Config.OUTPUT_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "Video not found"}), 404
    return send_file(file_path, mimetype="video/mp4", as_attachment=False)


@app.route("/api/download/<filename>")
def download_video(filename):
    """Download video as file."""
    file_path = Config.OUTPUT_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "Video not found"}), 404
    return send_file(file_path, mimetype="video/mp4", as_attachment=True, download_name=filename)


@app.route("/api/download_all_zip")
def download_all_zip():
    """Bundles all generated shorts into a single ZIP archive for one-click folder download."""
    if not Config.OUTPUT_DIR.exists():
        return jsonify({"error": "Output directory does not exist"}), 404

    mp4_files = sorted(Config.OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not mp4_files:
        return jsonify({"error": "No generated video clips found to download"}), 404

    # Remove any existing zip in temp
    for old_zip in Config.TEMP_DIR.glob("AutoClip_Shorts_*.zip"):
        try:
            old_zip.unlink(missing_ok=True)
        except Exception:
            pass

    zip_filename = f"AutoClip_Shorts_Batch_{int(time.time())}.zip"
    zip_path = Config.TEMP_DIR / zip_filename

    try:
        # ZIP_STORED: no re-compression overhead, instant creation (<0.2s), 0% CPU & zero RAM spikes
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            for mp4 in mp4_files:
                if mp4.is_file() and mp4.stat().st_size > 0:
                    zf.write(mp4, arcname=mp4.name)

        return send_file(
            zip_path,
            mimetype="application/zip",
            as_attachment=True,
            download_name="AutoClip_All_Shorts.zip",
        )
    except Exception as e:
        return jsonify({"error": f"Failed to package ZIP: {e}"}), 500


@app.route("/api/download_batch_zip/<job_id>")
def download_batch_zip(job_id):
    """Bundles only the clips generated in a specific job into a ZIP archive."""
    job = JOBS.get(job_id)
    if not job or not job.results:
        return download_all_zip()

    files_to_zip = []
    for r in job.results:
        f_path = Path(r["path"])
        if f_path.exists() and f_path.stat().st_size > 0:
            files_to_zip.append(f_path)

    if not files_to_zip:
        return download_all_zip()

    safe_name = "AutoClip_Job_Batch"
    zip_filename = f"{safe_name}_{job_id}.zip"
    zip_path = Config.TEMP_DIR / zip_filename

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            for f in files_to_zip:
                zf.write(f, arcname=f.name)

        return send_file(
            zip_path,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{safe_name}.zip",
        )
    except Exception as e:
        return jsonify({"error": f"Failed to package ZIP: {e}"}), 500


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json or {}
    url = data.get("youtube_url", "").strip()
    local_path = data.get("local_video_path", "").strip()
    if not url and not local_path:
        return jsonify({"error": "Please provide a valid YouTube URL or upload a local video file."}), 400

    job_id = str(uuid.uuid4())[:8]
    job = GenerationJob(job_id, data)
    JOBS[job_id] = job

    thread = threading.Thread(target=run_job_thread, args=(job,), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id, "status": "queued"})


@app.route("/api/status/<job_id>")
def get_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "logs": job.logs,
        "results": job.results,
    })


@app.route("/api/stream/<job_id>")
def stream_logs(job_id):
    """Server-Sent Events (SSE) stream for real-time progress and logs."""
    job = JOBS.get(job_id)
    if not job:
        return Response("event: error\ndata: Job not found\n\n", mimetype="text/event-stream")

    def event_stream():
        # First send all existing logs
        for l in job.logs:
            yield f"data: {json.dumps({'log': l, 'progress': job.progress, 'status': job.status})}\n\n"

        while True:
            try:
                msg = job.log_queue.get(timeout=1.0)
                if msg is None:  # Sentinel for done
                    yield f"data: {json.dumps({'done': True, 'status': job.status, 'progress': job.progress, 'results': job.results})}\n\n"
                    break
                yield f"data: {json.dumps({'log': msg, 'progress': job.progress, 'status': job.status})}\n\n"
            except queue.Empty:
                if job.status in ("completed", "failed"):
                    yield f"data: {json.dumps({'done': True, 'status': job.status, 'progress': job.progress, 'results': job.results})}\n\n"
                    break
                # Keep connection alive with heartbeat
                yield f": heartbeat\n\n"

    return Response(event_stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    })


if __name__ == "__main__":
    ensure_directories = Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 66)
    print("  🎬 AutoClip Studio Web App running at: http://localhost:5000")
    print("=" * 66 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
