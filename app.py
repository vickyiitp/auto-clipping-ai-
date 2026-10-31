"""
=============================================================================
  AutoClip Studio Ultra Pro — Enterprise Web Server & Multi-User Dispatcher
=============================================================================
  Modular Google Gemini Ultra Pro grade architecture:
  - Multi-user concurrency with session isolation (X-Session-ID)
  - Pure JavaScript Single Page Application dynamic rendering
  - Low-VRAM sequential hardware acceleration (QSV / NVENC / CPU)
  - 10-Route dynamic self-healing mesh with real-time SSE streaming
=============================================================================
"""

import os
import sys

# Ensure UTF-8 output encoding on Windows
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

os.environ["KMP_AFFINITY"] = "none"
os.environ.setdefault("OMP_NUM_THREADS", "6")
os.environ.setdefault("MKL_NUM_THREADS", "6")

import time
import json
import uuid
import queue
import threading
import zipfile
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, Response, send_file, send_from_directory

# Import from modular core package
from core.config import (
    Config,
    SUBTITLE_PRESETS,
    GENRE_THEMES,
    GOOGLE_FONTS_CATALOG,
    get_system_memory_info,
    purge_temp_cache,
    ensure_directories,
)
from core.biomimetic import (
    TOPOLOGY,
    LaminarMemoryGovernor,
    ROUTE_MESH,
)
from core.rendering import detect_hardware_encoder
from core.ingestion import (
    inspect_youtube_video,
    inspect_local_video,
)
from core.queue import BATCH_MANAGER, GenerationJob
from core.pipeline import process_video_pipeline

app = Flask(__name__, template_folder="templates", static_folder="static")

# Connect pipeline executor to batch manager
BATCH_MANAGER.set_pipeline_executor(process_video_pipeline)


@app.after_request
def add_performance_headers(response):
    """Adds HTTP Keep-Alive, static caching, and byte range headers."""
    if request.path.startswith("/static/js/") or request.path.startswith("/static/css/"):
        # Real-time studio development & live user interaction: never serve stale scripts
        response.headers["Cache-Control"] = "no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    elif request.path.startswith("/fonts/") or request.path.endswith((".woff2", ".woff", ".ttf")):
        response.headers["Cache-Control"] = "public, max-age=604800, immutable"
    elif request.path.startswith("/api/stream_video/") or request.path.startswith("/api/video/"):
        response.headers["Accept-Ranges"] = "bytes"
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response


# ──────────────────────────────────────────────────────────────────────────
# MAIN SINGLE PAGE APPLICATION MOUNT
# ──────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serves the pure JavaScript dynamic host shell with asset cache busting."""
    asset_version = int(time.time())
    return render_template("index.html", v=asset_version)


# ──────────────────────────────────────────────────────────────────────────
# SYSTEM STATUS & BIOMIMETIC TELEMETRY
# ──────────────────────────────────────────────────────────────────────────

@app.route("/api/system_status")
def system_status():
    """Returns live RAM, CPU %, hardware encoder, and 10-Route Mesh health."""
    mem_info = get_system_memory_info()
    laminar_state = LaminarMemoryGovernor.get_memory_state()
    temp_bytes = sum(f.stat().st_size for f in Config.TEMP_DIR.glob("*") if f.is_file()) if Config.TEMP_DIR.exists() else 0
    temp_mb = round(temp_bytes / (1024 * 1024), 1)

    routes = [
        {"code": "R1", "name": "Media Ingestion", "desc": "Split-merge yt-dlp -> Single Stream -> Cached match"},
        {"code": "R2", "name": "Vocal Extraction", "desc": "4-Pole 80-8000Hz bandpass -> Mono resample -> Stream copy"},
        {"code": "R3", "name": "Whisper STT", "desc": "P-Core pinned Faster-Whisper -> Batched pipeline -> Unfiltered fallback"},
        {"code": "R4", "name": "Clip Detection", "desc": "Ollama Llama-3 structured prompt -> Speech density scanner -> Uniform"},
        {"code": "R5", "name": "Auto-Reframe", "desc": "Apollo Kalman tracker -> Predictive gator -> Center crop"},
        {"code": "R6", "name": "HW Transcoding", "desc": "GPU Hardware (NVENC/QSV/AMF) -> libx264 CPU -> Safe crop"},
        {"code": "R7", "name": "ASS Typography", "desc": "Dual typography kinetic bounce -> Single line glow -> Raw text"},
        {"code": "R8", "name": "Memory Governor", "desc": "RAM floor monitoring -> Emergency temp cache flush -> Sequential pacing"},
        {"code": "R9", "name": "Core Affinity", "desc": "P-Core 4.90GHz affinity lock -> All cores balanced -> OpenMP auto"},
        {"code": "R10", "name": "Delivery Mesh", "desc": "SSD atomic rename -> Temp dir fallback -> Direct stream"},
    ]

    return jsonify({
        "status": "healthy",
        "system_memory": mem_info,
        "laminar_state": laminar_state,
        "topology": TOPOLOGY.get_summary(),
        "hardware_encoder": detect_hardware_encoder(),
        "route_mesh": ROUTE_MESH.get_mesh_status(),
        "routes": routes,
        "temp_cache_mb": temp_mb,
    })


@app.route("/api/purge_cache", methods=["POST"])
@app.route("/api/cleanup", methods=["POST"])
def cleanup_temp_cache():
    """Purges intermediate working files and forces garbage collection."""
    data = request.get_json(silent=True) or {}
    clear_models = data.get("clear_models", False)
    res = purge_temp_cache(clear_models=clear_models)
    return jsonify({
        "status": "success",
        "freed_mb": res.get("freed_mb", 0),
        "deleted_files": res.get("deleted_files", 0),
    })


# ──────────────────────────────────────────────────────────────────────────
# MEDIA INSPECTION & UPLOAD
# ──────────────────────────────────────────────────────────────────────────

@app.route("/api/inspect", methods=["POST"])
def inspect_video():
    """Inspect YouTube video metadata without downloading heavy media."""
    data = request.get_json(silent=True) or {}
    url = (data.get("youtube_url") or "").strip()
    if not url:
        return jsonify({"status": "error", "message": "No YouTube URL provided"}), 400

    info = inspect_youtube_video(url)
    return jsonify({
        "status": "success",
        "info": info,
        "title": info.get("title"),
        "duration": info.get("duration"),
        "duration_str": info.get("duration_str"),
        "thumbnail": info.get("thumbnail"),
        "max_height": info.get("max_height"),
        "quality_label": info.get("quality_label"),
        "has_ultra": info.get("has_ultra"),
        "boxes_30s": info.get("boxes_30s"),
    })


@app.route("/api/upload", methods=["POST"])
def upload_video():
    """Uploads local video from user machine and inspects metadata."""
    if "video" not in request.files:
        return jsonify({"status": "error", "message": "No video file provided"}), 400

    file = request.files["video"]
    if not file or file.filename == "":
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    ext = Path(file.filename).suffix.lower()
    allowed_exts = [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"]
    if ext not in allowed_exts:
        return jsonify({"status": "error", "message": f"Unsupported format '{ext}'. Allowed: {', '.join(allowed_exts)}"}), 400

    Config.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^\w\s-]", "", Path(file.filename).stem).strip().replace(" ", "_")
    safe_name = f"upload_{safe_stem[:35]}_{uuid.uuid4().hex[:6]}{ext}"
    save_path = Config.DOWNLOADS_DIR / safe_name
    file.save(str(save_path))

    meta = inspect_local_video(save_path)
    return jsonify({
        "status": "success",
        "file_path": str(save_path),
        "info": meta,
    })


@app.route("/api/thumb/<path:filename>")
def serve_thumbnail(filename):
    """Serves generated thumbnail previews from temp directory."""
    return send_from_directory(str(Config.TEMP_DIR), filename)


# ──────────────────────────────────────────────────────────────────────────
# MULTI-USER JOB GENERATION & DISPATCH
# ──────────────────────────────────────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def generate():
    """Submits a single video generation job with isolated session tracking."""
    session_id = request.headers.get("X-Session-ID") or "default"
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id") or session_id

    url = (data.get("youtube_url") or "").strip()
    local_path = (data.get("local_video_path") or "").strip()

    if not url and not local_path:
        return jsonify({"status": "error", "message": "Must provide a YouTube URL or local video."}), 400

    job_params = dict(data)
    job = BATCH_MANAGER.submit_job(job_params, session_id=session_id)

    return jsonify({
        "status": "success",
        "job_id": job.job_id,
        "session_id": session_id,
        "message": "Video job successfully submitted to fair queue.",
    })


@app.route("/api/batch_generate", methods=["POST"])
def batch_generate():
    """Submits multiple YouTube URLs simultaneously for batch queued execution."""
    session_id = request.headers.get("X-Session-ID") or "default"
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id") or session_id

    urls = data.get("urls") or []
    if isinstance(urls, str):
        urls = [u.strip() for u in urls.splitlines() if u.strip()]

    if not urls:
        return jsonify({"status": "error", "message": "No URLs provided in batch list."}), 400

    created_ids = []
    for single_url in urls:
        item_params = dict(data)
        item_params["youtube_url"] = single_url
        item_params["local_video_path"] = None
        item_params.pop("urls", None)
        job = BATCH_MANAGER.submit_job(item_params, session_id=session_id)
        created_ids.append(job.job_id)

    return jsonify({
        "status": "success",
        "queued_count": len(created_ids),
        "job_ids": created_ids,
        "message": f"Successfully queued {len(created_ids)} videos for processing.",
    })


@app.route("/api/queue_status")
@app.route("/api/queue")
def get_queue_status():
    """Returns waiting queue summary for the requesting user/session."""
    session_id = request.headers.get("X-Session-ID") or "default"
    all_jobs = BATCH_MANAGER.list_jobs(session_id=session_id)

    active_job = BATCH_MANAGER.get_active_job()
    active_data = active_job.to_dict() if active_job else None

    waiting_data = []
    idx = 1
    for j in all_jobs:
        if j["status"] in ("queued", "starting"):
            waiting_data.append({
                "position": idx,
                "job_id": j["job_id"],
                "title": j["video_title"],
                "genre": j.get("params", {}).get("genre", "Podcast"),
                "clipping_mode": j.get("params", {}).get("clipping_mode", "smart_highlights"),
                "status": j["status"],
            })
            idx += 1

    return jsonify({
        "is_active": active_job is not None,
        "current_job": active_data,
        "waiting_count": len(waiting_data),
        "waiting_jobs": waiting_data,
    })


@app.route("/api/job_status/<job_id>")
@app.route("/api/status/<job_id>")
def get_job_status(job_id):
    """Queries live execution state and progress for a single job."""
    job = BATCH_MANAGER.get_job(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found"}), 404

    return jsonify(job.to_dict())


@app.route("/api/cancel_job/<job_id>", methods=["POST"])
@app.route("/api/queue/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id):
    """Cancels a queued or executing job."""
    success = BATCH_MANAGER.cancel_job(job_id)
    return jsonify({"status": "success" if success else "failed", "job_id": job_id})


@app.route("/api/clear_queue", methods=["POST"])
@app.route("/api/queue/clear", methods=["POST"])
def clear_queue():
    """Clears all waiting jobs in queue."""
    session_id = request.headers.get("X-Session-ID")
    all_jobs = BATCH_MANAGER.list_jobs(session_id=session_id)
    cancelled = 0
    for j in all_jobs:
        if j["status"] == "queued":
            BATCH_MANAGER.cancel_job(j["job_id"])
            cancelled += 1

    return jsonify({"status": "success", "cancelled_count": cancelled})


# ──────────────────────────────────────────────────────────────────────────
# REAL-TIME SSE LOG STREAMING
# ──────────────────────────────────────────────────────────────────────────

@app.route("/api/stream_logs/<job_id>")
@app.route("/api/stream/<job_id>")
def stream_logs(job_id):
    """Server-Sent Events (SSE) live progress and log stream."""
    job = BATCH_MANAGER.get_job(job_id)
    if not job:
        return Response("event: error\ndata: Job not found\n\n", mimetype="text/event-stream")

    def event_stream():
        sent_index = 0
        while True:
            # Send any new logs added since last check
            current_logs = list(job.logs)
            if sent_index < len(current_logs):
                for line in current_logs[sent_index:]:
                    payload = {
                        "log": line,
                        "progress": job.progress,
                        "status": job.status,
                        "current_step": job.current_step,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                sent_index = len(current_logs)

            if job.status in ("completed", "failed", "cancelled"):
                final_payload = {
                    "done": True,
                    "status": job.status,
                    "progress": job.progress,
                    "current_step": job.current_step,
                    "output_files": job.output_files,
                }
                yield f"data: {json.dumps(final_payload)}\n\n"
                break

            time.sleep(0.4)

    return Response(event_stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


# ──────────────────────────────────────────────────────────────────────────
# GALLERY & DOWNLOAD ROUTES
# ──────────────────────────────────────────────────────────────────────────

@app.route("/api/gallery")
@app.route("/api/videos")
def get_gallery():
    """Lists all rendered 9:16 vertical shorts from output directory."""
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shorts = []
    for f in sorted(Config.OUTPUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        st = f.stat()
        shorts.append({
            "filename": f.name,
            "title": f.stem,
            "size_mb": round(st.st_size / (1024 * 1024), 2),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
            "stream_url": f"/api/stream_video/{f.name}",
            "download_url": f"/api/download/{f.name}",
        })
    return jsonify({"status": "success", "shorts": shorts, "videos": shorts})


@app.route("/api/stream_video/<path:filename>")
@app.route("/api/video/<path:filename>")
def stream_video(filename):
    """Serves 9:16 vertical video for smooth HTML5 browser preview."""
    file_path = (Config.OUTPUT_DIR / filename).resolve()
    if not file_path.exists() or not str(file_path).startswith(str(Config.OUTPUT_DIR.resolve())):
        return jsonify({"error": "Video file not found"}), 404
    return send_file(file_path, mimetype="video/mp4", as_attachment=False)


@app.route("/api/download/<path:filename>")
def download_video(filename):
    """Direct file download of single short."""
    file_path = (Config.OUTPUT_DIR / filename).resolve()
    if not file_path.exists() or not str(file_path).startswith(str(Config.OUTPUT_DIR.resolve())):
        return jsonify({"error": "Video file not found"}), 404
    return send_file(file_path, mimetype="video/mp4", as_attachment=True, download_name=file_path.name)


@app.route("/api/download_zip")
@app.route("/api/download_all_zip")
def download_all_zip():
    """Bundles all generated shorts into a single ZIP for 1-click download."""
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mp4_files = sorted(Config.OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not mp4_files:
        return jsonify({"status": "error", "message": "No shorts found to download."}), 404

    zip_filename = f"AutoClip_Shorts_Bundle_{int(time.time())}.zip"
    zip_path = Config.TEMP_DIR / zip_filename
    Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
        for f in mp4_files:
            zf.write(f, arcname=f.name)

    return send_file(zip_path, mimetype="application/zip", as_attachment=True, download_name="AutoClip_Shorts.zip")


@app.route("/api/delete_short/<path:filename>", methods=["POST", "DELETE"])
def delete_short(filename):
    """Deletes short permanently from output directory."""
    file_path = (Config.OUTPUT_DIR / filename).resolve()
    if file_path.exists() and str(file_path).startswith(str(Config.OUTPUT_DIR.resolve())):
        try:
            file_path.unlink()
            return jsonify({"status": "success", "filename": filename})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "File not found"}), 404


if __name__ == "__main__":
    ensure_directories()
    print("\n" + "=" * 70, flush=True)
    print("  🚀 AutoClip Studio Ultra Pro (Waitress WSGI)", flush=True)
    print("  Google Gemini Ultra Pro Inspired Enterprise Multi-User Architecture", flush=True)
    print("  Serving at: http://localhost:5000", flush=True)
    print("=" * 70 + "\n", flush=True)
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=5000, threads=16, channel_timeout=120)
    except ImportError:
        app.run(host="0.0.0.0", port=5000, debug=False)
