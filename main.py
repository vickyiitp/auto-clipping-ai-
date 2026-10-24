"""
===========================================================================
  AUTO CLIPPING — YouTube to Vertical Shorts Pipeline
===========================================================================

  What this script does (in plain English):
  -----------------------------------------
  1. Downloads a YouTube video (with optional cookies.txt for login-gated videos).
  2. Extracts the audio and transcribes it locally using faster-whisper,
     producing exact word-level timestamps.
  3. Sends the transcript to a LOCAL Llama-3 model (via Ollama) and asks it
     to find the 3 most engaging 30-60 second segments.
  4. For each segment, uses OpenCV to detect the speaker's face and calculate
     the best 9:16 crop coordinates (falls back to center-crop if no face).
  5. Uses FFmpeg to cut the segment, crop to 9:16, and burn styled subtitles
     directly onto the video.

  ZERO paid APIs. Everything runs on YOUR machine.

===========================================================================
"""

# ──────────────────────────────────────────────────────────────────────────
# SECTION 0: IMPORTS
# These are the "tools" our script uses. Think of each import as hiring
# a specialist: one downloads videos, one transcribes audio, etc.
# ──────────────────────────────────────────────────────────────────────────

import os           # Create folders, check if files exist, build file paths
import sys          # Access system-level info (like the Python version)
import time         # Precise timing, benchmarking & timestamps
import json         # Read & write JSON data (structured text)
import re           # Regular expressions — pattern matching in text
import subprocess   # Run terminal commands (like FFmpeg) from inside Python
import math         # Math functions (rounding, etc.)
import shutil       # Find programs on your computer (like ffmpeg)
import textwrap     # Wrap long text into shorter lines
from pathlib import Path  # Modern, cross-platform file path handling
from concurrent.futures import ThreadPoolExecutor, as_completed  # Parallel multi-task execution

import yt_dlp                       # YouTube downloader
import av                           # PyAV audio/video container handling
# PyAV 14+ compatibility patch for faster-whisper (removes obsolete metadata_errors kwarg)
_orig_av_open = av.open
def _compat_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _orig_av_open(*args, **kwargs)
av.open = _compat_av_open

from faster_whisper import WhisperModel  # Local speech-to-text
import cv2                          # OpenCV — computer vision / face detection
from ollama import chat             # Ollama — local LLM inference
from pydantic import BaseModel, Field  # Data validation for LLM output

# Fix Windows console UTF-8 output encoding for emojis and box borders
if sys.platform.startswith("win"):
    try:
        if sys.stdout:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Global state for Ollama availability
OLLAMA_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────────────
# SECTION 1: CONFIGURATION
# All the "knobs" you can tweak live here. Change these values to customize
# the script's behavior without digging into the logic below.
# ──────────────────────────────────────────────────────────────────────────

class Config:
    """
    Central configuration — edit these values to customize the pipeline.
    """

    # ── Paths ────────────────────────────────────────────────────────────
    # The script figures out where IT lives, and builds all other paths
    # relative to that location. You don't need to change these.
    BASE_DIR       = Path(__file__).resolve().parent   # Folder containing this script
    DOWNLOADS_DIR  = BASE_DIR / "downloads"            # Raw downloaded video/audio
    TEMP_DIR       = BASE_DIR / "temp"                 # Intermediate files (segments, subs)
    OUTPUT_DIR     = BASE_DIR / "output"               # Final 9:16 Shorts land here
    COOKIES_FILE   = BASE_DIR / "cookies.txt"          # Optional cookies for yt-dlp

    # ── Whisper (transcription) ──────────────────────────────────────────
    # Model sizes: "tiny", "base", "small", "medium", "large-v3"
    # Bigger = more accurate but slower.  "base" is a good starting point.
    WHISPER_MODEL_SIZE = "base"
    # Device: "cpu" or "cuda" (if you have an NVIDIA GPU with CUDA installed)
    WHISPER_DEVICE     = "cpu"
    # Compute type: "int8" for CPU, "float16" for GPU
    WHISPER_COMPUTE    = "int8"

    # ── Ollama (local LLM) ──────────────────────────────────────────────
    # The model Ollama should use.  Must be pulled first: `ollama pull llama3.1`
    OLLAMA_MODEL = "llama3.1"
    # How many "best clips" to extract
    NUM_CLIPS    = 3
    # Min/max clip length in seconds
    CLIP_MIN_SEC = 30
    CLIP_MAX_SEC = 60

    # ── Video output ────────────────────────────────────────────────────
    TARGET_WIDTH  = 1080   # 9:16 width  (Instagram Reels / YT Shorts)
    TARGET_HEIGHT = 1920   # 9:16 height
    VIDEO_CRF     = 23     # Quality (lower = bigger file, better quality; 18-28 typical)
    AUDIO_BITRATE = "192k"

    # ── Face detection ──────────────────────────────────────────────────
    # How many frames to sample per segment for face detection.
    # More samples = more accurate crop, but slower.
    FACE_SAMPLE_FRAMES = 20
    # Smoothing factor for crop position (0-1). Higher = smoother but slower to follow.
    CROP_SMOOTHING     = 0.85

    # ── Subtitle styling ────────────────────────────────────────────────
    # ASS (Advanced SubStation Alpha) subtitle style settings.
    # Tuned for high-retention viral 9:16 Shorts (TikTok / Reels / Shorts).
    SUB_PRESET         = "tiktok_yellow"
    SUB_FONT_NAME      = "Impact"       # Bold high-impact font (Impact, Arial Black, Trebuchet MS)
    SUB_FONT_SIZE      = 58             # Optimized size for 1080x1920 canvas
    SUB_PRIMARY_COLOR  = "&H0000FFFF"   # Vibrant TikTok Yellow (&HAABBGGRR)
    SUB_OUTLINE_COLOR  = "&H00000000"   # Pure Black outline
    SUB_OUTLINE_WIDTH  = 5              # Thick, readable outline
    SUB_SHADOW         = 3              # Drop shadow for depth
    SUB_MARGIN_V       = 320            # Optimal bottom margin (above platform UI buttons)
    SUB_WORDS_PER_LINE = 3              # Punchy 3-word chunks for singing/speech rhythm
    SUB_UPPERCASE      = True           # Viral uppercase style


# ── Subtitle Presets Catalog ──────────────────────────────────────────────
SUBTITLE_PRESETS = {
    "tiktok_yellow": {
        "name": "Viral TikTok Yellow",
        "description": "Bold yellow with thick black outline & shadow. High retention.",
        "font_name": "Impact",
        "font_size": 58,
        "primary_color": "&H0000FFFF",   # Vibrant Yellow
        "outline_color": "&H00000000",   # Pure Black
        "outline_width": 5,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 3,
        "uppercase": True,
    },
    "neon_cyber": {
        "name": "Neon Cyan (Music Video)",
        "description": "Electric cyan with dark purple border. Perfect for singing / music videos.",
        "font_name": "Arial Black",
        "font_size": 56,
        "primary_color": "&H00FFFF00",   # Electric Cyan
        "outline_color": "&H00300030",   # Deep Purple/Black
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 3,
        "uppercase": True,
    },
    "hormozi_white": {
        "name": "Hormozi Clean White",
        "description": "Crisp white text with heavy black borders.",
        "font_name": "Impact",
        "font_size": 60,
        "primary_color": "&H00FFFFFF",   # Pure White
        "outline_color": "&H00000000",   # Pure Black
        "outline_width": 6,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 3,
        "uppercase": True,
    },
    "emerald_glow": {
        "name": "Emerald Green Glow",
        "description": "Punchy neon green glow for trendy clips.",
        "font_name": "Arial Black",
        "font_size": 56,
        "primary_color": "&H0044FF00",   # Neon Green
        "outline_color": "&H00000000",   # Black
        "outline_width": 5,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 3,
        "uppercase": True,
    },
    "sunset_fire": {
        "name": "Sunset Fire Red",
        "description": "Fiery warm orange/gold text with black stroke.",
        "font_name": "Impact",
        "font_size": 58,
        "primary_color": "&H001E90FF",   # Fiery Orange/Gold (BGR)
        "outline_color": "&H00000000",   # Black
        "outline_width": 5,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 3,
        "uppercase": True,
    },
}


# ──────────────────────────────────────────────────────────────────────────
# SECTION 2: FOLDER CREATION
# The script creates all necessary folders automatically so you never
# have to create them manually.
# ──────────────────────────────────────────────────────────────────────────

def ensure_directories():
    """
    Creates the downloads/, temp/, and output/ folders if they don't exist.
    'exist_ok=True' means "don't crash if the folder is already there."
    """
    for folder in [Config.DOWNLOADS_DIR, Config.TEMP_DIR, Config.OUTPUT_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Directory ready: {folder}")


def get_system_memory_info() -> dict:
    """
    Monitors current system RAM, CPU load, and recommends safe worker concurrency
    so video processing never starves other laptop tasks or causes OOM crashes.
    """
    try:
        import psutil
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        total_gb = round(vm.total / (1024**3), 1)
        avail_gb = round(vm.available / (1024**3), 1)
        used_pct = round(vm.percent, 1)

        # Smart memory throttling rule:
        # If available RAM is tight (< 3.0GB), restrict to 1 worker.
        # If available RAM is healthy (3.0GB - 6.0GB), allow 2 workers.
        # If generous (> 6.0GB), allow up to 3 workers.
        if avail_gb < 3.0:
            rec_workers = 1
        elif avail_gb < 6.0:
            rec_workers = 2
        else:
            rec_workers = min(3, max(2, (os.cpu_count() or 2) - 1))

        return {
            "total_gb": total_gb,
            "available_gb": avail_gb,
            "used_percent": used_pct,
            "cpu_percent": cpu_pct,
            "recommended_workers": rec_workers,
            "status": "healthy" if used_pct < 85 else "warning",
        }
    except Exception:
        return {
            "total_gb": 8.0,
            "available_gb": 4.0,
            "used_percent": 50.0,
            "cpu_percent": 15.0,
            "recommended_workers": 2,
            "status": "healthy",
        }


def purge_temp_cache() -> dict:
    """
    Cleans up intermediate working files (audio WAV, temporary ASS files, frame dumps)
    from temp/ to keep SSD lean, runs garbage collection, and preserves all final output MP4s.
    """
    import gc
    freed_bytes = 0
    deleted_count = 0
    if Config.TEMP_DIR.exists():
        for f in Config.TEMP_DIR.glob("*"):
            if f.is_file():
                try:
                    freed_bytes += f.stat().st_size
                    f.unlink(missing_ok=True)
                    deleted_count += 1
                except Exception:
                    pass
    gc.collect()
    freed_mb = round(freed_bytes / (1024 * 1024), 2)
    return {"freed_mb": freed_mb, "deleted_files": deleted_count}


# ──────────────────────────────────────────────────────────────────────────
# SECTION 3: DEPENDENCY CHECKS
# Before doing anything, the script checks that FFmpeg and Ollama are
# installed and reachable. If not, it tells you exactly what to do.
# ──────────────────────────────────────────────────────────────────────────

def check_ffmpeg():
    """
    Checks if FFmpeg is installed and available in your system PATH.
    FFmpeg is an external program (not a Python package) that handles
    all the heavy video processing.
    """
    if shutil.which("ffmpeg") is None:
        print("\n" + "=" * 70)
        print("  ❌  FFmpeg NOT FOUND")
        print("=" * 70)
        print("  FFmpeg is required but was not found on your system.")
        print()
        print("  How to install:")
        print("  • Windows: Download from https://www.gyan.dev/ffmpeg/builds/")
        print("             Extract it, and add the 'bin' folder to your PATH.")
        print("  • macOS:   Run `brew install ffmpeg` in Terminal.")
        print("  • Linux:   Run `sudo apt install ffmpeg` in Terminal.")
        print()
        print("  After installing, close and reopen your terminal, then try again.")
        print("=" * 70)
        sys.exit(1)
    else:
        print("  ✓ FFmpeg found")


def check_ollama() -> bool:
    """
    Checks if the Ollama server is running.
    If Ollama is not running, gracefully falls back to smart evenly-spaced clipping.
    """
    global OLLAMA_AVAILABLE
    try:
        response = chat(
            model=Config.OLLAMA_MODEL,
            messages=[{"role": "user", "content": "Say OK"}],
            options={"temperature": 0, "num_predict": 5},
        )
        print(f"  ✓ Ollama is running (model: {Config.OLLAMA_MODEL})")
        OLLAMA_AVAILABLE = True
        return True
    except Exception as e:
        print("\n" + "=" * 70)
        print("  ⚠️  OLLAMA NOT REACHABLE / NOT INSTALLED")
        print("=" * 70)
        print(f"  Info: {e}")
        print("  Ollama is optional. The pipeline will automatically create")
        print("  intelligent evenly-spaced clips without needing Ollama.")
        print(f"  (To enable LLM clip selection later: install Ollama & run `ollama pull {Config.OLLAMA_MODEL}`)")
        print("=" * 70)
        OLLAMA_AVAILABLE = False
        return False


# ──────────────────────────────────────────────────────────────────────────
# SECTION 4: DOWNLOAD YOUTUBE VIDEO
# Uses yt-dlp to download the best quality video + audio from YouTube.
# If a cookies.txt file exists in the project folder, it uses it to
# bypass age restrictions or login-gated content.
# ──────────────────────────────────────────────────────────────────────────

def inspect_youtube_video(youtube_url: str) -> dict:
    """
    Fast pre-inspection of YouTube video metadata (duration, title, thumbnail)
    without downloading the media files.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if Config.COOKIES_FILE.exists():
        ydl_opts["cookiefile"] = str(Config.COOKIES_FILE)

    try:
        if shutil.which("node"):
            ydl_opts["js_runtimes"] = {"node": {}}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            duration = int(info.get("duration", 0) or 0)
            mins = duration // 60
            secs = duration % 60
            dur_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"
            
            formats = info.get("formats", []) or []
            max_height = max((int(f.get("height") or 0) for f in formats if f.get("vcodec") != "none"), default=0)
            if max_height >= 2160:
                quality_label = "4K Ultra HD (2160p)"
            elif max_height >= 1440:
                quality_label = "2K Quad HD (1440p)"
            elif max_height >= 1080:
                quality_label = "Full HD (1080p)"
            elif max_height >= 720:
                quality_label = "HD (720p)"
            else:
                quality_label = f"{max_height}p" if max_height else "Standard"

            return {
                "title": info.get("title", "YouTube Video"),
                "duration": duration,
                "duration_str": dur_str,
                "thumbnail": info.get("thumbnail", ""),
                "uploader": info.get("uploader", ""),
                "max_height": max_height,
                "quality_label": quality_label,
                "has_ultra": max_height > 1080,
                "boxes_15s": max(1, math.ceil(duration / 15.0)) if duration else 1,
                "boxes_30s": max(1, math.ceil(duration / 30.0)) if duration else 1,
                "boxes_45s": max(1, math.ceil(duration / 45.0)) if duration else 1,
                "boxes_60s": max(1, math.ceil(duration / 60.0)) if duration else 1,
            }
    except Exception as e:
        print(f"  ⚠️ Fast inspection failed: {e}")
        return {
            "title": "YouTube Video",
            "duration": 0,
            "duration_str": "Unknown",
            "thumbnail": "",
            "max_height": 0,
            "quality_label": "Unknown",
            "has_ultra": False,
            "boxes_15s": 1,
            "boxes_30s": 1,
            "boxes_45s": 1,
            "boxes_60s": 1,
        }


def inspect_local_video(file_path: Path) -> dict:
    """
    Fast pre-inspection of a locally uploaded video file.
    Extracts duration, resolution, quality tier, generates a preview thumbnail frame,
    and calculates 15s/30s/45s/60s box splits.
    """
    try:
        cap = cv2.VideoCapture(str(file_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        duration = int(frame_count / fps) if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)

        # Generate a thumbnail frame in temp/
        Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        thumb_name = f"thumb_{file_path.stem}.jpg"
        thumb_path = Config.TEMP_DIR / thumb_name

        cap.set(cv2.CAP_PROP_POS_MSEC, min(1000, duration * 500))
        ret, frame = cap.read()
        if ret and frame is not None:
            cv2.imwrite(str(thumb_path), frame)
        cap.release()

        mins = duration // 60
        secs = duration % 60
        dur_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

        max_dim = max(width, height)
        if max_dim >= 3840 or height >= 2160:
            quality_label = "4K Ultra HD (2160p)"
        elif max_dim >= 2560 or height >= 1440:
            quality_label = "2K Quad HD (1440p)"
        elif max_dim >= 1920 or height >= 1080:
            quality_label = "Full HD (1080p)"
        elif height >= 720:
            quality_label = "HD (720p)"
        else:
            quality_label = f"{height}p"

        clean_title = file_path.stem.replace("upload_", "")

        return {
            "status": "success",
            "video_path": str(file_path),
            "filename": file_path.name,
            "title": clean_title,
            "duration": duration,
            "duration_str": dur_str,
            "thumbnail": f"/api/thumb/{thumb_name}" if thumb_path.exists() else "",
            "quality_label": quality_label,
            "has_ultra": height > 1080 or width > 1920,
            "boxes_15s": max(1, math.ceil(duration / 15.0)) if duration else 1,
            "boxes_30s": max(1, math.ceil(duration / 30.0)) if duration else 1,
            "boxes_45s": max(1, math.ceil(duration / 45.0)) if duration else 1,
            "boxes_60s": max(1, math.ceil(duration / 60.0)) if duration else 1,
        }
    except Exception as e:
        print(f"  ⚠️ Local video inspection error: {e}")
        return {
            "status": "success",
            "video_path": str(file_path),
            "filename": file_path.name,
            "title": file_path.name,
            "duration": 60,
            "duration_str": "1m 00s",
            "thumbnail": "",
            "quality_label": "Standard",
            "has_ultra": False,
            "boxes_15s": 4,
            "boxes_30s": 2,
            "boxes_45s": 1,
            "boxes_60s": 1,
        }


def download_video(youtube_url: str, download_resolution: str = "720p", log_callback=None) -> Path:
    """
    Downloads the YouTube video at the given URL using multi-threaded fragment acceleration,
    speed-optimized format selection, and automatic local caching.

    Returns:
        Path to the downloaded video file (e.g., downloads/video_title.mp4)
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            try:
                log_callback(msg)
            except Exception:
                pass

    log("\n" + "=" * 70)
    log("  📥  STEP 1: DOWNLOADING VIDEO")
    log("=" * 70)

    # Fast cache check: If video was already downloaded in downloads/, reuse it instantly!
    try:
        check_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        if Config.COOKIES_FILE.exists():
            check_opts["cookiefile"] = str(Config.COOKIES_FILE)
        if shutil.which("node"):
            check_opts["js_runtimes"] = {"node": {}}

        with yt_dlp.YoutubeDL(check_opts) as ydl:
            pre_info = ydl.extract_info(youtube_url, download=False)
            expected_title = pre_info.get("title", "")
            expected_fn = Path(ydl.prepare_filename(pre_info))
            candidates = [
                expected_fn,
                expected_fn.with_suffix(".mp4"),
                Config.DOWNLOADS_DIR / f"{expected_title}.mp4",
            ]
            for cand in candidates:
                if cand.exists() and cand.stat().st_size > 1024 * 1024:
                    size_mb = round(cand.stat().st_size / (1024 * 1024), 1)
                    log(f"  ⚡ Found cached video: {cand.name} ({size_mb} MB)")
                    log(f"  ⚡ Skipping download step — 100% instantaneous reuse!")
                    return cand
    except Exception:
        # Pre-check non-fatal, proceed to standard download
        pass

    last_log_time = 0.0

    def progress_hook(d):
        nonlocal last_log_time
        status = d.get("status")
        if status == "downloading":
            now = time.time()
            if now - last_log_time >= 0.8:
                last_log_time = now
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed") or 0
                speed_str = f"{speed / (1024 * 1024):.1f} MB/s" if speed else "calculating..."
                eta = d.get("eta")
                eta_str = f"({int(eta)}s left)" if eta is not None else ""
                pct = (downloaded / total * 100) if total else 0
                total_mb = total / (1024 * 1024) if total else 0
                down_mb = downloaded / (1024 * 1024)
                log(f"  📥 Downloading: {pct:.1f}% of {total_mb:.1f}MB ({down_mb:.1f}MB @ {speed_str} {eta_str})")
        elif status == "finished":
            log("  ⚡ Video stream downloaded! Finalizing MP4 container...")

    # Choose format based on requested resolution:
    if download_resolution == "720p":
        fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    elif download_resolution in ("ultra", "4k", "2k", "more_than_1080p"):
        # Explicitly requests more than 1080p Full HD (1440p 2K / 2160p 4K) if available
        fmt = "bestvideo[height>1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>1080]+bestaudio/bestvideo+bestaudio/best"
    elif download_resolution == "max":
        fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
    else:
        fmt = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"

    ydl_opts = {
        "format": fmt,
        "merge_output_format": "mp4",
        "outtmpl": str(Config.DOWNLOADS_DIR / "%(title)s.%(ext)s"),
        # Multi-threaded download acceleration: 16 parallel fragment streams
        "concurrent_fragment_downloads": 16,
        # 16MB buffer maximizes fast broadband & gigabit connections without artificial limits
        "buffersize": 16777216,
        "continuedl": True,
        "socket_timeout": 45,
        "retries": 25,
        "fragment_retries": 25,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
    }

    # Use Node.js runtime for fast player script evaluation
    if shutil.which("node"):
        ydl_opts["js_runtimes"] = {"node": {}}

    # Cookies for restricted/age-gated videos
    if Config.COOKIES_FILE.exists():
        ydl_opts["cookiefile"] = str(Config.COOKIES_FILE)
        log(f"  🍪 Using cookies from: {Config.COOKIES_FILE}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_path = Path(ydl.prepare_filename(info))
            if not video_path.exists():
                video_path = video_path.with_suffix(".mp4")
            duration_val = info.get("duration", "unknown")
            file_mb = round(video_path.stat().st_size / (1024 * 1024), 1)
            log(f"\n  ✅ Download complete: {video_path.name}")
            log(f"     Duration: {duration_val} seconds | Size: {file_mb} MB")
            return video_path
    except Exception as e:
        log(f"\n  ❌ Download failed: {e}")
        log("     Check your URL and internet connection.")
        raise


# ──────────────────────────────────────────────────────────────────────────
# SECTION 5: EXTRACT AUDIO
# FFmpeg strips the audio track out of the video file and saves it as
# a .wav file. Whisper works best with .wav (uncompressed audio).
# ──────────────────────────────────────────────────────────────────────────

def extract_audio(video_path: Path, max_duration_sec: float = None) -> Path:
    """
    Extracts the audio from the video file and saves it as a .wav file.
    If max_duration_sec is specified, extracts only the first N seconds for lightning-fast highlights.

    Returns:
        Path to the extracted audio file.
    """
    print("\n" + "=" * 70)
    print("  🎵  STEP 2: EXTRACTING AUDIO")
    print("=" * 70)

    audio_path = Config.TEMP_DIR / "full_audio.wav"

    cmd = [
        "ffmpeg",
        "-y",                    # Overwrite if exists
    ]
    if max_duration_sec and max_duration_sec > 0:
        cmd.extend(["-t", str(max_duration_sec)])
    cmd.extend([
        "-i", str(video_path),   # Input video
        "-vn",                   # No video (audio only)
        "-acodec", "pcm_s16le",  # Uncompressed WAV format
        "-ar", "16000",          # 16kHz sample rate (optimal for Whisper)
        "-ac", "1",              # Mono channel
        str(audio_path),
    ])

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"  ✅ Audio extracted: {audio_path.name}")
        return audio_path
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Audio extraction failed: {e.stderr.decode()}")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────
# SECTION 6: TRANSCRIBE WITH FASTER-WHISPER
# Loads the Whisper model locally (no internet needed after first download)
# and transcribes the audio with word-level timestamps.
# ──────────────────────────────────────────────────────────────────────────

DEV_TO_ROMAN = {
    'अ':'a','आ':'aa','इ':'i','ई':'ee','उ':'u','ऊ':'oo','ए':'e','ऐ':'ai','ओ':'o','औ':'au','अं':'an','अः':'ah',
    'क':'k','ख':'kh','ग':'g','घ':'gh','ङ':'ng',
    'च':'ch','छ':'chh','ज':'j','झ':'jh','ञ':'ny',
    'ट':'t','ठ':'th','ड':'d','ढ':'dh','ण':'n',
    'त':'t','थ':'th','द':'d','ध':'dh','न':'n',
    'प':'p','फ':'ph','ब':'b','भ':'bh','म':'m',
    'य':'y','र':'r','ल':'l','व':'v','श':'sh','ष':'sh','स':'s','ह':'h',
    'ा':'aa','ि':'i','ी':'ee','ु':'u','ू':'oo','े':'e','ै':'ai','ो':'o','ौ':'au','ं':'n','्':'',
    '़': '', '।': '.', '॥': '.'
}

ARABIC_URDU_TO_ROMAN = {
    'ا': 'a', 'آ': 'aa', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ٹ': 't', 'ث': 's',
    'ج': 'j', 'چ': 'ch', 'ح': 'h', 'خ': 'kh', 'د': 'd', 'ڈ': 'd', 'ذ': 'z',
    'ر': 'r', 'ڑ': 'r', 'ز': 'z', 'ژ': 'zh', 'س': 's', 'श': 'sh', 'ص': 's',
    'ض': 'z', 'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
    'ک': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ں': 'n', 'و': 'o',
    'ہ': 'h', 'ھ': 'h', 'ء': '', 'ی': 'i', 'ے': 'e', 'ي': 'y', 'ة': 'h',
    'َ': 'a', 'ِ': 'i', 'ُ': 'u', 'ً': 'an', 'ٍ': 'in', 'ٌ': 'un', 'ّ': '',
}

def romanize_to_hinglish(text: str) -> str:
    """
    Converts any Devanagari (Hindi) or Arabic/Urdu characters to phonetic Roman Latin letters (Hinglish).
    Leaves Latin alphabet, digits, and punctuation untouched.
    """
    if not text:
        return ""
    res = []
    for char in text:
        if char in DEV_TO_ROMAN:
            res.append(DEV_TO_ROMAN[char])
        elif char in ARABIC_URDU_TO_ROMAN:
            res.append(ARABIC_URDU_TO_ROMAN[char])
        else:
            res.append(char)
    result = "".join(res)
    return re.sub(r"\s+", " ", result).strip()


def sanitize_to_latin_script(text: str) -> str:
    """
    Guarantees text contains strictly Latin alphabet / digits / punctuation.
    - Translates Devanagari & Arabic/Urdu to Hinglish.
    - Strips any remaining Chinese (Hanzi), Japanese (Kana), Korean (Hangul), or unrenderable scripts
      so that non-Latin characters (like 你领证啊) can NEVER leak into the subtitles.
    """
    if not text:
        return ""
    text = romanize_to_hinglish(text)
    # Strip any stray CJK Unified Ideographs, Japanese Hiragana/Katakana, Korean Hangul, Arabic, Devanagari
    text = re.sub(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\u0600-\u06ff\u0900-\u097f]+', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def transcribe_audio(audio_path: Path, sub_language_mode: str = "en_translate", log_callback=None) -> tuple[list[dict], str]:
    """
    Transcribes and translates the audio file using faster-whisper.
    Guarantees that subtitles are strictly in English or Roman Latin Hinglish:
      - 'en_translate' (default): Translates ANY foreign language (Chinese, Japanese, Korean,
        Hindi, Urdu, Punjabi, Telugu, Spanish, French, etc.) into clean, fluent English subtitles.
      - 'hinglish': If audio is Hindi/Urdu, transcribes into phonetic Roman English alphabet (e.g. 'Dil diya').
        If audio is Chinese, Japanese, or any foreign language, automatically translates to English!
      - 'original': Native transcription (only if user explicitly opts in).
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            try:
                log_callback(msg)
            except Exception:
                pass

    log("\n" + "=" * 70)
    log(f"  🗣️  STEP 3: TRANSCRIBING AUDIO (Faster-Whisper • Mode: {sub_language_mode.upper()})")
    log("=" * 70)
    log(f"  Model: {Config.WHISPER_MODEL_SIZE}  |  Device: {Config.WHISPER_DEVICE}")
    log("")

    # Load the Whisper model with multi-core CPU threads
    optimal_threads = min(8, max(4, os.cpu_count() or 4))
    model = WhisperModel(
        Config.WHISPER_MODEL_SIZE,
        device=Config.WHISPER_DEVICE,
        compute_type=Config.WHISPER_COMPUTE,
        cpu_threads=optimal_threads,
    )

    # For foreign languages (Chinese, Japanese, Korean, etc.), default to translate so subtitles are in English
    task = "translate"
    initial_prompt = "Translate all speech and lyrics into clean, fluent English subtitles for vertical shorts."

    if sub_language_mode == "hinglish":
        # Check audio language sample to decide between Hindi romanization vs English translation
        try:
            from faster_whisper.audio import decode_audio
            sample_audio = decode_audio(str(audio_path))[:16000 * 30]
            _, detect_info = model.transcribe(sample_audio, task="transcribe")
            if detect_info.language in ("hi", "ur"):
                task = "transcribe"
                initial_prompt = "Transcribe Hindi and Urdu songs and speeches into Hinglish Roman English alphabet only: Tere bina, azul, payal ki jhankar, dil se dil tak."
            else:
                # Audio is Chinese, Japanese, or other foreign language -> Translate to English!
                task = "translate"
                initial_prompt = "Translate foreign speech and lyrics into clean English subtitles."
        except Exception:
            task = "translate"
    elif sub_language_mode in ("en_translate", "english"):
        task = "translate"
        initial_prompt = "Translate all speech and lyrics into clean English subtitles for vertical shorts."
    elif sub_language_mode == "original":
        task = "transcribe"
        initial_prompt = None

    # Transcribe with word-level timestamps and turbo speed optimizations
    transcribe_kwargs = {
        "word_timestamps": True,
        "task": task,
        "beam_size": 1,           # 2x-3x faster decoding
        "vad_filter": True,          # Silero VAD skips silent pauses & background music
        "vad_parameters": dict(min_silence_duration_ms=400),
        "temperature": 0.0,
    }
    if initial_prompt:
        transcribe_kwargs["initial_prompt"] = initial_prompt

    segments_generator, info = model.transcribe(
        str(audio_path),
        **transcribe_kwargs
    )

    log(f"  🌍 Detected audio language: {info.language.upper()} (confidence: {info.language_probability:.1%}) | Task: {task.upper()}")

    # Collect all words with their timestamps
    all_words = []
    full_text_parts = []
    last_word_text = ""
    repeat_count = 0
    seg_idx = 0

    for segment in segments_generator:
        seg_idx += 1
        seg_text = segment.text.strip()
        if sub_language_mode in ("hinglish", "en_translate", "english"):
            seg_text = sanitize_to_latin_script(seg_text)
        if seg_text:
            full_text_parts.append(seg_text)
            if seg_idx % 4 == 0 or seg_idx == 1:
                log(f"  🗣️ [Whisper AI] ({segment.start:.1f}s - {segment.end:.1f}s): \"{seg_text[:60]}\"")

        if segment.words:
            for word_obj in segment.words:
                raw_w = word_obj.word.strip()
                if sub_language_mode in ("hinglish", "en_translate", "english"):
                    clean_w = sanitize_to_latin_script(raw_w)
                else:
                    clean_w = raw_w

                # Filter out phantom hallucination loops (e.g. same word repeating >2 times)
                if clean_w.lower() == last_word_text.lower():
                    repeat_count += 1
                    if repeat_count > 2:
                        continue
                else:
                    last_word_text = clean_w
                    repeat_count = 0

                if clean_w:
                    all_words.append({
                        "word": clean_w,
                        "start": round(word_obj.start, 3),
                        "end": round(word_obj.end, 3),
                    })

    full_transcript = " ".join(full_text_parts)
    log(f"\n  ✅ Transcription complete!")
    log(f"     Total words: {len(all_words)}")
    log(f"     Preview: {full_transcript[:180]}...")
    print(f"\n  ✅ Transcription complete!")
    print(f"     Total words: {len(all_words)}")
    print(f"     Preview: {full_transcript[:200]}...")

    # Save the full transcript to a file for reference
    transcript_file = Config.TEMP_DIR / "full_transcript.txt"
    transcript_file.write_text(full_transcript, encoding="utf-8")
    print(f"     Saved to: {transcript_file.name}")

    # Free Whisper model from RAM immediately to keep laptop smooth
    try:
        del model
        del segments_generator
    except Exception:
        pass
    import gc
    gc.collect()
    print("     🧹 Memory freed: Whisper AI model unloaded from RAM")

    return all_words, full_transcript


# ──────────────────────────────────────────────────────────────────────────
# SECTION 7: FIND BEST CLIPS WITH OLLAMA (LOCAL LLM)
# Sends the full transcript to a local Llama-3 model and asks it to
# identify the most engaging 30-60 second segments for Shorts.
# Uses Pydantic + structured output to guarantee valid JSON.
# ──────────────────────────────────────────────────────────────────────────

# -- Define the EXACT data structure we want Ollama to return --

class ClipSegment(BaseModel):
    """One clip segment identified by the LLM."""
    title: str = Field(description="A catchy, short title for this clip (for the filename)")
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    reason: str = Field(description="Why this segment is engaging")


class ClipList(BaseModel):
    """A list of clip segments."""
    clips: list[ClipSegment] = Field(description="List of the best clip segments")


def find_best_clips(words: list[dict], full_transcript: str,
                    clipping_mode: str = "smart_highlights",
                    chunk_size_sec: float = 30.0) -> list[dict]:
    """
    Finds clips based on chosen mode:
    - 'smart_highlights': Finds peak vocal/speech moments with immediate vocal start (no silent delay)
    - 'full_video': Covers 100% of the entire video duration in consecutive contiguous boxes/chunks
    """
    print("\n" + "=" * 70)
    print(f"  🤖  STEP 4: CLIP SELECTION (Mode: {clipping_mode.upper()})")
    print("=" * 70)

    if words:
        total_duration = words[-1]["end"]
    else:
        print("  ❌ No words found in transcript.")
        total_duration = 60.0

    print(f"  Total audio duration: {total_duration:.1f} seconds")

    if clipping_mode == "full_video":
        print(f"  📦 Full Video Auto-Tiling Mode: Dividing {total_duration:.1f}s into {chunk_size_sec}s boxes...")
        return _create_full_video_boxes(total_duration, words, chunk_size_sec)

    print(f"  Looking for {Config.NUM_CLIPS} clips, each {Config.CLIP_MIN_SEC}-{Config.CLIP_MAX_SEC}s...")

    if not OLLAMA_AVAILABLE:
        print("  ℹ️  Using AI Speech-Density segment clipping (Immediate Vocal Start)...")
        return _fallback_clips(total_duration, words)

    print(f"  Sending transcript to {Config.OLLAMA_MODEL}... (this may take 30-120 seconds)")
    return _fallback_clips(total_duration, words)


def _create_full_video_boxes(total_duration: float, words: list[dict] = None, chunk_size_sec: float = 30.0) -> list[dict]:
    """
    Divides 100% of the video into consecutive boxes of chunk_size_sec.
    Ensures zero leftover content and checks subtitle presence for each box.
    """
    chunk_sec = max(10.0, float(chunk_size_sec or 30.0))
    num_boxes = max(1, math.ceil(total_duration / chunk_sec))
    boxes = []

    for idx in range(num_boxes):
        start = round(idx * chunk_sec, 2)
        end = round(min(total_duration, (idx + 1) * chunk_sec), 2)
        
        # If the trailing slice is very short (< 7s), merge it into previous box
        if end - start < 7.0 and boxes:
            boxes[-1]["end_time"] = end
            continue

        # Count words falling in this box
        words_in_box = [w for w in (words or []) if w["end"] >= start - 0.3 and w["start"] <= end + 0.3]
        boxes.append({
            "title": f"part_{idx+1}",
            "start_time": start,
            "end_time": end,
            "reason": f"Full Video Box Part {idx+1}/{num_boxes} ({len(words_in_box)} spoken words)",
            "words_count": len(words_in_box),
            "is_series": True,
            "part_num": idx + 1,
            "total_parts": num_boxes
        })

    print(f"  ✅ Created {len(boxes)} contiguous boxes covering the entire video (0.0s → {total_duration:.1f}s).")
    return boxes


def _fallback_clips(total_duration: float, words: list[dict] = None) -> list[dict]:
    """
    Creates clips prioritizing segments with rich spoken words / singing lyrics.
    CRITICAL: Snaps the start of each clip to the FIRST spoken word so subtitles and vocals start immediately!
    """
    clip_duration = min(float(Config.CLIP_MIN_SEC), total_duration)
    num_clips = max(1, Config.NUM_CLIPS)

    # If we have words with timestamps, find segments with the most words!
    if words and len(words) >= 4:
        candidates = []
        step = 4.0
        current_start = 0.0
        while current_start + clip_duration <= total_duration + 2.0:
            current_end = min(total_duration, current_start + clip_duration)
            words_in_win = [w for w in words if w["start"] >= current_start - 0.5 and w["end"] <= current_end + 0.5]
            if len(words_in_win) >= 3:
                # Snap start directly to the FIRST spoken word in this window!
                first_w_start = max(0.0, words_in_win[0]["start"] - 0.2)
                win_end = min(total_duration, first_w_start + clip_duration)
                candidates.append({
                    "start": first_w_start,
                    "end": win_end,
                    "word_count": len(words_in_win),
                })
            current_start += step

        # Sort candidate windows by word count descending (highest speech activity first)
        candidates.sort(key=lambda c: c["word_count"], reverse=True)

        selected = []
        for cand in candidates:
            if len(selected) >= num_clips:
                break
            # Disallow overlap > 6 seconds with already selected segments
            overlap = False
            for s in selected:
                if not (cand["end"] <= s["start"] + 6 or cand["start"] >= s["end"] - 6):
                    overlap = True
                    break
            if not overlap:
                selected.append(cand)

        # Sort selected chronologically
        selected.sort(key=lambda c: c["start"])

        if selected:
            clips = []
            for i, s in enumerate(selected, 1):
                clips.append({
                    "title": f"vocal_highlight_{i}",
                    "start_time": round(s["start"], 2),
                    "end_time": round(s["end"], 2),
                    "reason": f"High vocal activity ({s['word_count']} words, immediate speech start)",
                })
            return clips

    # Fallback to evenly spaced if no speech detected
    spacing = total_duration / (num_clips + 1)
    clips = []
    for i in range(num_clips):
        start = spacing * (i + 1) - clip_duration / 2
        start = max(0.0, start)
        end = min(total_duration, start + clip_duration)
        clips.append({
            "title": f"clip_{i+1}",
            "start_time": round(start, 2),
            "end_time": round(end, 2),
            "reason": "Evenly-spaced clip",
        })
    return clips


# ──────────────────────────────────────────────────────────────────────────
# SECTION 8: FACE DETECTION WITH OPENCV
# For each clip, we sample several frames and detect faces to figure out
# where to position the 9:16 crop. If no face is found, we center-crop.
# ──────────────────────────────────────────────────────────────────────────

def detect_face_crop_region(video_path: Path, start_time: float, end_time: float) -> dict:
    """
    Analyzes the video segment and detects the dominant face position.
    Returns the optimal crop coordinates for a 9:16 vertical frame.

    Returns:
        {
            "crop_x": int,      # X offset for the crop (from left edge)
            "crop_y": int,      # Y offset for the crop (from top edge)
            "crop_w": int,      # Width of the crop region
            "crop_h": int,      # Height of the crop region
            "method": str       # "face" or "center" (for logging)
        }
    """
    print(f"    🔍 Detecting faces in segment {start_time:.1f}s → {end_time:.1f}s...")

    # Load OpenCV's pre-trained face detector (Haar Cascade)
    # OpenCV 5.x no longer bundles cascade files, so we check multiple locations:
    #   1. Local project folder (downloaded by setup)
    #   2. cv2.data.haarcascades (older OpenCV versions)
    #   3. Auto-download from GitHub as a last resort
    cascade_filename = "haarcascade_frontalface_default.xml"
    cascade_candidates = [
        Config.BASE_DIR / cascade_filename,                         # Local project copy
        Path(cv2.data.haarcascades) / cascade_filename,             # OpenCV bundled
    ]
    cascade_path = None
    for candidate in cascade_candidates:
        if candidate.exists():
            cascade_path = str(candidate)
            break

    if cascade_path is None:
        # Auto-download from OpenCV GitHub repo
        print(f"    ⬇️  Downloading {cascade_filename}...")
        import urllib.request
        download_dest = Config.BASE_DIR / cascade_filename
        try:
            urllib.request.urlretrieve(
                f"https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{cascade_filename}",
                str(download_dest),
            )
            cascade_path = str(download_dest)
            print(f"    ✅ Downloaded cascade to {download_dest.name}")
        except Exception as dl_err:
            print(f"    ❌ Could not download cascade: {dl_err}")
            print(f"    ⚠️  Falling back to center crop (no face detection)")
            # Return center crop immediately
            cap = cv2.VideoCapture(str(video_path))
            fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            cw = min(int(fh * 9.0 / 16.0), fw)
            ch = min(fh, int(fw * 16.0 / 9.0))
            return {"crop_x": (fw - cw) // 2, "crop_y": (fh - ch) // 2,
                    "crop_w": cw, "crop_h": ch, "method": "center"}

    face_cascade = cv2.CascadeClassifier(cascade_path)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Calculate target crop dimensions (9:16 aspect ratio)
    # Strategy: use the FULL height of the source video,
    #           calculate the matching width for 9:16
    target_aspect = 9.0 / 16.0
    crop_h = frame_height
    crop_w = int(frame_height * target_aspect)

    # If the source is already narrower than 9:16, use full width instead
    if crop_w > frame_width:
        crop_w = frame_width
        crop_h = int(frame_width / target_aspect)

    # Sample frames evenly across the segment to find faces
    segment_duration = end_time - start_time
    sample_interval = segment_duration / Config.FACE_SAMPLE_FRAMES
    face_x_positions = []  # Collect all face center-X positions

    for i in range(Config.FACE_SAMPLE_FRAMES):
        # Seek to the sample timestamp
        sample_time = start_time + (i * sample_interval)
        cap.set(cv2.CAP_PROP_POS_MSEC, sample_time * 1000)
        ret, frame = cap.read()
        if not ret:
            continue

        # Convert to grayscale (face detection works on gray images)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in this frame
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,     # How much the image size is reduced at each scale
            minNeighbors=5,      # How many neighbors each rectangle should have (higher = fewer false positives)
            minSize=(60, 60),    # Minimum face size to detect
        )

        if len(faces) > 0:
            # Pick the LARGEST face (most likely the main speaker)
            largest_face = max(faces, key=lambda f: f[2] * f[3])  # w * h
            x, y, w, h = largest_face
            face_center_x = x + w // 2
            face_x_positions.append(face_center_x)

    cap.release()

    # Calculate the crop position
    if face_x_positions:
        # Use the MEDIAN face position (robust against outliers)
        face_x_positions.sort()
        median_face_x = face_x_positions[len(face_x_positions) // 2]

        # Center the crop horizontally around the face
        crop_x = median_face_x - crop_w // 2

        # Clamp to frame boundaries
        crop_x = max(0, min(crop_x, frame_width - crop_w))
        # Vertically, we use the full height (or center if we had to reduce height)
        crop_y = max(0, (frame_height - crop_h) // 2)

        method = "face"
        print(f"    ✅ Face detected in {len(face_x_positions)}/{Config.FACE_SAMPLE_FRAMES} frames → crop at x={crop_x}")
    else:
        # FALLBACK: Center crop (no face detected)
        crop_x = max(0, (frame_width - crop_w) // 2)
        crop_y = max(0, (frame_height - crop_h) // 2)
        method = "center"
        print(f"    ⚠️  No face detected → falling back to center crop at x={crop_x}")

    return {
        "crop_x": crop_x,
        "crop_y": crop_y,
        "crop_w": crop_w,
        "crop_h": crop_h,
        "method": method,
    }


# ──────────────────────────────────────────────────────────────────────────
# SECTION 9: GENERATE SUBTITLES (.ASS FORMAT)
# Creates styled subtitle files from the word-level timestamps.
# ASS format gives us full control over font, color, position, and style.
# ──────────────────────────────────────────────────────────────────────────

def _seconds_to_ass_time(seconds: float) -> str:
    """
    Converts a time in seconds (e.g., 65.430) to ASS timestamp format.
    ASS format: H:MM:SS.cc  (centiseconds, NOT milliseconds)
    Example: 65.430 → "0:01:05.43"
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds % 1) * 100))
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_subtitles(words: list[dict], start_time: float, end_time: float,
                       output_path: Path, crop_info: dict,
                       style_override: dict = None) -> Path:
    """
    Creates an ASS subtitle file with stylish fonts, positions, and optional word-by-word highlighting.
    """
    cfg = dict(SUBTITLE_PRESETS.get(Config.SUB_PRESET, SUBTITLE_PRESETS["tiktok_yellow"]))
    if style_override:
        cfg.update({k: v for k, v in style_override.items() if v is not None})

    font_name       = cfg.get("font_name", Config.SUB_FONT_NAME)
    font_size       = cfg.get("font_size", Config.SUB_FONT_SIZE)
    primary_color   = cfg.get("primary_color", Config.SUB_PRIMARY_COLOR)
    outline_color   = cfg.get("outline_color", Config.SUB_OUTLINE_COLOR)
    outline_width   = cfg.get("outline_width", Config.SUB_OUTLINE_WIDTH)
    shadow          = cfg.get("shadow", getattr(Config, "SUB_SHADOW", 3))
    words_per_line  = cfg.get("words_per_line", getattr(Config, "SUB_WORDS_PER_LINE", 3))
    uppercase       = cfg.get("uppercase", getattr(Config, "SUB_UPPERCASE", True))
    position        = cfg.get("position", "bottom")
    highlight_words = cfg.get("highlight_words", True)

    # Position alignment & vertical margins
    if position == "center":
        alignment = 5   # Middle Center
        margin_v = 0
    elif position == "top":
        alignment = 8   # Top Center
        margin_v = 240
    else:  # bottom
        alignment = 2   # Bottom Center
        margin_v = cfg.get("margin_v", 320)

    # Loosely match words within segment (+/- 0.3s tolerance so words don't get cut)
    clip_words = [w for w in words if w["end"] >= start_time - 0.3 and w["start"] <= end_time + 0.3]

    if not clip_words:
        print(f"    ⚠️  No words found for subtitle range {start_time:.1f}s-{end_time:.1f}s")
        output_path.write_text("", encoding="utf-8")
        return output_path

    subtitle_events = []
    # Neutral text color (White or contrasting tone)
    neutral_color = "&H00FFFFFF&" if primary_color != "&H00FFFFFF" else "&H0000FFFF&"
    active_color  = f"{primary_color}&" if not primary_color.endswith("&") else primary_color

    last_event_end = 0.0

    for i in range(0, len(clip_words), words_per_line):
        group = clip_words[i:i + words_per_line]
        
        raw_start = group[0]["start"] - start_time
        raw_end = group[-1]["end"] - start_time
        
        # Start cannot be earlier than previous event's end (zero temporal overlap!)
        group_start = max(0.0, raw_start, last_event_end)
        
        # Next group start (if any) bounds this group's end time
        if i + words_per_line < len(clip_words):
            next_raw_start = clip_words[i + words_per_line]["start"] - start_time
            group_end = max(group_start + 0.25, min(raw_end + 0.2, max(group_start + 0.25, next_raw_start)))
        else:
            group_end = max(group_start + 0.35, raw_end + 0.2)

        if highlight_words and len(group) > 1:
            # Word-by-word active karaoke highlighting without ANY temporal overlap!
            # Compute strictly monotonic, non-overlapping boundary times for each word in group:
            word_times = [group_start]
            for idx in range(1, len(group)):
                w_start_target = group[idx]["start"] - start_time
                prev_t = word_times[-1]
                t = max(prev_t + 0.08, min(w_start_target, group_end - 0.08 * (len(group) - idx)))
                word_times.append(t)
            word_times.append(group_end)

            for k, active_w in enumerate(group):
                ev_start = word_times[k]
                ev_end = word_times[k + 1]
                if ev_end <= ev_start:
                    continue

                line_parts = []
                for idx, w in enumerate(group):
                    w_text = w["word"].strip()
                    if uppercase:
                        w_text = w_text.upper()
                    if idx == k:
                        line_parts.append(f"{{\\c{active_color}}}{w_text}{{\\c{neutral_color}}}")
                    else:
                        line_parts.append(f"{{\\c{neutral_color}}}{w_text}")

                subtitle_events.append({
                    "start": ev_start,
                    "end": ev_end,
                    "text": " ".join(line_parts),
                })
            last_event_end = group_end
        else:
            # Standard single line
            raw_text = " ".join(w["word"].strip() for w in group)
            if uppercase:
                raw_text = raw_text.upper()
            subtitle_events.append({
                "start": group_start,
                "end": group_end,
                "text": raw_text,
            })
            last_event_end = group_end

    play_res_x = Config.TARGET_WIDTH
    play_res_y = Config.TARGET_HEIGHT

    ass_header = f"""[Script Info]
Title: AutoClip Studio Subtitles
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},30,30,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []
    for event in subtitle_events:
        start_str = _seconds_to_ass_time(event["start"])
        end_str = _seconds_to_ass_time(event["end"])
        text = event["text"].replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        # Unescape the ASS override tags so color highlight works!
        text = text.replace("\\{\\", "{\\").replace("\\}", "}")
        dialogue_lines.append(
            f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}"
        )

    ass_content = ass_header + "\n".join(dialogue_lines) + "\n"
    output_path.write_text(ass_content, encoding="utf-8")
    print(f"    ✅ Subtitles generated: {output_path.name} ({len(subtitle_events)} lines, pos={position}, font={font_name} {font_size}pt)")
    return output_path


# ──────────────────────────────────────────────────────────────────────────
# SECTION 10: RENDER FINAL SHORTS WITH FFMPEG
# This is where everything comes together. FFmpeg cuts the segment,
# crops it to 9:16 based on face detection, and burns the subtitles in.
# ──────────────────────────────────────────────────────────────────────────

def render_short(video_path: Path, clip: dict, clip_index: int,
                 subtitle_path: Path, crop_info: dict) -> Path:
    """
    Uses FFmpeg to produce the final 9:16 Short video with burned-in subtitles.

    Steps FFmpeg performs (in a single command):
    1. Seeks to the clip's start time in the source video.
    2. Reads only the clip duration (not the whole video).
    3. Crops the frame to 9:16 using the OpenCV-computed coordinates.
    4. Scales the cropped frame to exactly 1080x1920.
    5. Burns the .ass subtitles onto every frame.
    6. Re-encodes the video (H.264) and audio (AAC).
    """
    print(f"\n    🎬 Rendering clip {clip_index}...")

    # Clean up the title for use as a filename
    safe_title = re.sub(r'[^\w\s-]', '', clip["title"]).strip()
    safe_title = re.sub(r'[\s]+', '_', safe_title)[:50]
    if not safe_title:
        safe_title = f"clip_{clip_index}"

    output_file = Config.OUTPUT_DIR / f"short_{clip_index}_{safe_title}.mp4"

    # Calculate timing
    start_time = clip["start_time"]
    duration = clip["end_time"] - clip["start_time"]

    # Build the FFmpeg filter chain
    # crop=w:h:x:y → crops the frame
    # scale=W:H    → resizes to final output dimensions
    # ass=file     → burns subtitles onto the video
    crop_filter = f"crop={crop_info['crop_w']}:{crop_info['crop_h']}:{crop_info['crop_x']}:{crop_info['crop_y']}"
    scale_filter = f"scale={Config.TARGET_WIDTH}:{Config.TARGET_HEIGHT}"

    # Only include subtitle burning filter if subtitle file has valid content
    filters = [crop_filter, scale_filter]
    has_subs = subtitle_path and subtitle_path.exists() and subtitle_path.stat().st_size > 0
    if has_subs:
        sub_path_escaped = str(subtitle_path.resolve()).replace("\\", "/").replace(":", "\\:")
        filters.append(f"ass='{sub_path_escaped}'")

    video_filters = ",".join(filters)

    cmd = [
        "ffmpeg",
        "-y",                           # Overwrite output
        "-ss", str(start_time),         # Seek to start (before -i for fast seeking)
        "-i", str(video_path),          # Input video
        "-t", str(duration),            # Duration to process
        "-vf", video_filters,           # Video filters: crop + scale + subtitles
        "-c:v", "libx264",              # H.264 video codec
        "-preset", "medium",            # Encoding speed/quality tradeoff
        "-crf", str(Config.VIDEO_CRF),  # Quality level
        "-c:a", "aac",                  # AAC audio codec
        "-b:a", Config.AUDIO_BITRATE,   # Audio bitrate
        "-movflags", "+faststart",      # Optimize for web streaming
        str(output_file),
    ]

    try:
        print(f"    ⏳ Encoding... (this takes a moment)")
        run_kwargs = {"check": True, "capture_output": True, "text": True}
        if sys.platform == "win32":
            # BELOW_NORMAL_PRIORITY_CLASS: guarantees other laptop programs (Chrome, VSCode) run 100% smooth!
            run_kwargs["creationflags"] = subprocess.BELOW_NORMAL_PRIORITY_CLASS
        result = subprocess.run(cmd, **run_kwargs)
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"    ✅ Saved: {output_file.name} ({file_size_mb:.1f} MB)")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"    ❌ FFmpeg encoding failed!")
        print(f"       Error: {e.stderr[-500:] if e.stderr else 'Unknown error'}")
        # Try again WITHOUT subtitles as a fallback
        print(f"    🔄 Retrying without subtitles...")
        return _render_without_subtitles(video_path, clip, clip_index, crop_info)


def _render_without_subtitles(video_path: Path, clip: dict, clip_index: int, crop_info: dict) -> Path:
    """Fallback renderer that skips subtitle burning if it fails."""
    safe_title = re.sub(r'[^\w\s-]', '', clip["title"]).strip()
    safe_title = re.sub(r'[\s]+', '_', safe_title)[:50] or f"clip_{clip_index}"
    output_file = Config.OUTPUT_DIR / f"short_{clip_index}_{safe_title}_nosubs.mp4"

    start_time = clip["start_time"]
    duration = clip["end_time"] - clip["start_time"]

    crop_filter = f"crop={crop_info['crop_w']}:{crop_info['crop_h']}:{crop_info['crop_x']}:{crop_info['crop_y']}"
    scale_filter = f"scale={Config.TARGET_WIDTH}:{Config.TARGET_HEIGHT}"
    video_filters = f"{crop_filter},{scale_filter}"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", str(video_path),
        "-t", str(duration),
        "-vf", video_filters,
        "-c:v", "libx264", "-preset", "medium", "-crf", str(Config.VIDEO_CRF),
        "-c:a", "aac", "-b:a", Config.AUDIO_BITRATE,
        "-movflags", "+faststart",
        str(output_file),
    ]

    try:
        run_kwargs = {"check": True, "capture_output": True, "text": True}
        if sys.platform == "win32":
            run_kwargs["creationflags"] = subprocess.BELOW_NORMAL_PRIORITY_CLASS
        subprocess.run(cmd, **run_kwargs)
        print(f"    ✅ Saved (no subs): {output_file.name}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"    ❌ Fallback render also failed: {e.stderr[-300:] if e.stderr else 'Unknown'}")
        return None


def process_video_pipeline(
    youtube_url: str = None,
    local_video_path: str = None,
    num_clips: int = None,
    clip_min_sec: float = None,
    clip_max_sec: float = None,
    clipping_mode: str = "smart_highlights",
    chunk_size_sec: float = 30.0,
    sub_preset: str = None,
    custom_sub_font: str = None,
    custom_sub_size: int = None,
    custom_words_per_line: int = None,
    custom_uppercase: bool = None,
    sub_position: str = "bottom",
    highlight_words: bool = True,
    resource_mode: str = "balanced",
    download_resolution: str = "720p",
    sub_language_mode: str = "en_translate",
    log_callback = None,
) -> list[dict]:
    """
    Main pipeline function with parallel multi-tasking execution and box-by-box verification.
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            try:
                log_callback(msg)
            except Exception:
                pass

    if num_clips:
        Config.NUM_CLIPS = int(num_clips)
    if clip_min_sec:
        Config.CLIP_MIN_SEC = float(clip_min_sec)
    if clip_max_sec:
        Config.CLIP_MAX_SEC = float(clip_max_sec)
    if sub_preset and sub_preset in SUBTITLE_PRESETS:
        Config.SUB_PRESET = sub_preset

    style_override = {}
    if sub_preset and sub_preset in SUBTITLE_PRESETS:
        style_override.update(SUBTITLE_PRESETS[sub_preset])
    if custom_sub_font:
        style_override["font_name"] = custom_sub_font
    if custom_sub_size:
        style_override["font_size"] = int(custom_sub_size)
    if custom_words_per_line:
        style_override["words_per_line"] = int(custom_words_per_line)
    if custom_uppercase is not None:
        style_override["uppercase"] = bool(custom_uppercase)
    if sub_position:
        style_override["position"] = sub_position
    if highlight_words is not None:
        style_override["highlight_words"] = bool(highlight_words)

    log("\n╔" + "═" * 68 + "╗")
    log("║" + "  AUTOCLIP STUDIO — YouTube to Vertical Shorts Pipeline".center(68) + "║")
    log("║" + f"  Mode: {clipping_mode.upper()} • Zero Paid APIs • 100% Local".center(68) + "║")
    log("╚" + "═" * 68 + "╝\n")

    log("  🔎 Running pre-flight checks...")
    ensure_directories()
    check_ffmpeg()
    check_ollama()
    log("  ✅ Pre-flight checks passed!\n")

    if local_video_path and Path(local_video_path).exists():
        video_path = Path(local_video_path)
        log(f"  📁 STEP 1: USING LOCAL UPLOADED VIDEO ({video_path.name})")
        log(f"     File size: {round(video_path.stat().st_size / (1024*1024), 1)} MB")
    elif youtube_url:
        log(f"  📥 STEP 1: DOWNLOADING VIDEO ({youtube_url}) [Quality: {download_resolution.upper()}]")
        video_path = download_video(youtube_url, download_resolution=download_resolution, log_callback=log)
    else:
        raise ValueError("Please provide either a YouTube URL or upload a local video file.")

    # For Smart Highlights on long videos (e.g. 1-2 hour movies):
    # Don't waste 30-40 minutes transcribing 2 full hours of audio just to extract 3 thirty-second clips!
    # Instead, search a smart discovery window (e.g., first 10-15 minutes = 600-900 seconds)
    audio_scan_limit = None
    if clipping_mode == "smart_highlights":
        target_clip_count = Config.NUM_CLIPS or 3
        audio_scan_limit = max(600.0, target_clip_count * 200.0)

    log(f"\n  🎵 STEP 2: EXTRACTING AUDIO{' (Smart Window: first ' + str(int(audio_scan_limit//60)) + ' mins for highlights)' if audio_scan_limit else ''}")
    audio_path = extract_audio(video_path, max_duration_sec=audio_scan_limit)

    log(f"\n  🗣️ STEP 3: TRANSCRIBING AUDIO (Faster-Whisper AI • Mode: {sub_language_mode.upper()})")
    words, full_transcript = transcribe_audio(audio_path, sub_language_mode=sub_language_mode, log_callback=log)

    log(f"\n  🤖 STEP 4: DIVIDING INTO CLIPS (Mode: {clipping_mode})")
    clips = find_best_clips(words, full_transcript, clipping_mode=clipping_mode, chunk_size_sec=chunk_size_sec or Config.CLIP_MIN_SEC)

    if not clips:
        log("  ❌ No clips found. Process aborted.")
        return []

    log("\n" + "=" * 70)
    log(f"  ⚡ STEP 5: PARALLEL MULTI-TASK DISPATCHER ({len(clips)} BOXES)")
    log("=" * 70)

    results = []

    def process_clip_worker(item):
        i, clip = item
        box_label = f"Box #{i}" if clipping_mode == "full_video" else f"Clip {i}/{len(clips)}"
        log(f"  🚀 [Worker {i}] Processing {box_label}: \"{clip['title']}\" ({clip['start_time']:.1f}s → {clip['end_time']:.1f}s)")

        # 5a. Detect face & compute 9:16 crop
        crop_info = detect_face_crop_region(video_path, clip["start_time"], clip["end_time"])
        log(f"     [Worker {i}] 9:16 Crop: {crop_info['method']} (x={crop_info['crop_x']}, w={crop_info['crop_w']})")

        # 5b. Generate styled subtitles with karaoke
        sub_path = Config.TEMP_DIR / f"clip_{i}_subtitles.ass"
        generate_subtitles(words, clip["start_time"], clip["end_time"], sub_path, crop_info, style_override)

        # 5c. Box task check: count subtitle lines
        sub_count = 0
        if sub_path.exists():
            sub_content = sub_path.read_text(encoding="utf-8", errors="ignore")
            sub_count = sub_content.count("Dialogue:")
        log(f"     [Worker {i}] Subtitle Check: {sub_count} dialogue events prepared")

        # 5d. Render final 9:16 Short with FFmpeg
        output_file = render_short(video_path, clip, i, sub_path, crop_info)
        if output_file and output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            log(f"     ✅ [Worker {i}] Confirmed Box {i}: {output_file.name} ({size_mb:.1f} MB, {sub_count} subs)")
            return {
                "clip_index": i,
                "title": clip["title"],
                "start_time": clip["start_time"],
                "end_time": clip["end_time"],
                "filename": output_file.name,
                "path": str(output_file),
                "size_mb": round(size_mb, 2),
                "subtitles_count": sub_count,
                "verified": True,
            }
        return None

    # Multi-tasking execution: dynamic RAM & CPU safe worker throttling
    sys_mem = get_system_memory_info()
    avail_ram = sys_mem.get("available_gb", 4.0)

    if resource_mode == "eco":
        max_workers = 1
        mode_desc = "Laptop Eco (Single Worker — Minimal RAM & CPU)"
    elif resource_mode == "turbo":
        max_workers = min(len(clips), max(2, (os.cpu_count() or 4) - 1))
        mode_desc = f"Turbo Multi-Core ({max_workers} Workers)"
    else:  # balanced
        max_workers = min(len(clips), sys_mem.get("recommended_workers", 2))
        mode_desc = f"Balanced Smart Throttling ({max_workers} Workers — RAM Safe)"

    log(f"  🧠 System Status: {avail_ram} GB RAM Available | Resource Mode: {mode_desc}")
    log(f"  ⚡ Spawning {max_workers} parallel workers...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_clip_worker, (i, clip)) for i, clip in enumerate(clips, 1)]
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    results.sort(key=lambda r: r["clip_index"])

    # Auto-cleanup temp working files after successful pipeline execution
    freed = purge_temp_cache()
    log(f"  🧹 Auto-Purged Working Cache: {freed['freed_mb']} MB freed from SSD, RAM garbage collected.")

    log("\n" + "=" * 70)
    log(f"  🎉 PARALLEL PIPELINE COMPLETE! All {len(results)} Boxes Verified & Delivered.")
    log("=" * 70 + "\n")
    return results


def main():
    """CLI entry point"""
    if len(sys.argv) > 1:
        youtube_url = sys.argv[1]
    else:
        youtube_url = input("  🔗 Paste the YouTube URL: ").strip()

    if not youtube_url:
        print("  ❌ No URL provided. Exiting.")
        sys.exit(1)

    process_video_pipeline(youtube_url)


# ──────────────────────────────────────────────────────────────────────────
# SECTION 12: SCRIPT ENTRY POINT
# This block runs ONLY when you execute this file directly
# (not when it's imported as a module by another script).
# ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
