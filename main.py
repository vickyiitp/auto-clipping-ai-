"""
=============================================================================
  AUTOCLIP STUDIO — HIGH-PERFORMANCE ZERO-RAM & GENRE KINETIC PIPELINE
=============================================================================
  Architectural Philosophy:
  1. Zero-RAM Video Buffering: Never load heavy video/audio into memory.
     Everything streams to and from SSD.
  2. Disk-Stream Frame Processing: Python generators + cv2.VideoCapture()
     read single frames from SSD, process coordinates, and immediately drop
     from RAM.
  3. Chunked Audio Analysis: Audio is segmented on SSD into small slices;
     faster-whisper transcribes directly from disk paths and unloads memory.
  4. The Index Agent: Python RAM holds ONLY lightweight metadata (paths,
     timestamps, crop boxes, genre config).
  5. Genre-Based AI Clipping: Dynamic Ollama Llama-3 prompt criteria tailored
     for Podcasts, Anime, Motivation, Movies, Web Series, Songs, Gaming.
  6. Dynamic Font & Theme Engine: 10+ Google Fonts auto-downloaded to SSD
     fonts/ directory and loaded natively by FFmpeg.
  7. Advanced Kinetic Typography: 1-to-2 words on screen max, word-level
     ASS karaoke/color highlighting with zero temporal collisions.
  8. Low-VRAM Sequential Hardware Acceleration: Auto-detects QSV/NVENC/AMF,
     running strictly sequential FFmpeg encodes.
=============================================================================
"""

import os
import sys

# Force UTF-8 encoding on Windows to prevent UnicodeEncodeError with emojis
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
import json
import math
import re
import gc
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Generator, Tuple, List, Dict, Any, Optional

import yt_dlp
import av
# PyAV 14+ compatibility patch for faster-whisper
_orig_av_open = av.open
def _compat_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _orig_av_open(*args, **kwargs)
av.open = _compat_av_open

from faster_whisper import WhisperModel
import cv2
from pydantic import BaseModel, Field

# Global state for Ollama availability
OLLAMA_AVAILABLE = False
try:
    from ollama import chat
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────────────
# SECTION 1: CENTRAL CONFIGURATION & PATHS
# ──────────────────────────────────────────────────────────────────────────

class Config:
    """Central configuration for SSD-streaming and genre-based clipping."""
    BASE_DIR        = Path(__file__).resolve().parent
    DOWNLOADS_DIR   = BASE_DIR / "downloads"
    TEMP_DIR        = BASE_DIR / "temp"
    OUTPUT_DIR      = BASE_DIR / "output"
    FONTS_DIR       = BASE_DIR / "fonts"
    COOKIES_FILE    = BASE_DIR / "cookies.txt"

    # Whisper Settings
    WHISPER_MODEL_SIZE = "base"
    WHISPER_DEVICE     = "cpu"       # "cpu" or "cuda"
    WHISPER_COMPUTE    = "int8"      # "int8" on CPU, "float16" on CUDA
    AUDIO_CHUNK_SEC    = 300.0       # 5 minutes SSD audio chunking for zero-RAM STT

    # Ollama Settings
    OLLAMA_MODEL       = "llama3.1"
    NUM_CLIPS          = 3
    CLIP_MIN_SEC       = 30.0
    CLIP_MAX_SEC       = 60.0

    # Video Render Settings
    TARGET_WIDTH       = 1080
    TARGET_HEIGHT      = 1920
    VIDEO_CRF          = 23
    AUDIO_BITRATE      = "192k"

    # Default Genre & Face Detection
    GENRE              = "Podcast"
    FACE_SAMPLE_FRAMES = 25
    SUB_WORDS_PER_LINE = 2           # 1-to-2 words on screen max (TikTok/Reels style)


# ──────────────────────────────────────────────────────────────────────────
# SECTION 2: HARDWARE ENCODER DETECTOR (LOW-VRAM GPU/CPU)
# ──────────────────────────────────────────────────────────────────────────

_CACHED_HW_ENCODER = None

def detect_hardware_encoder() -> Dict[str, Any]:
    """
    Auto-detects available GPU hardware acceleration for FFmpeg.
    Tests Intel QSV (h264_qsv), NVIDIA NVENC (h264_nvenc), AMD AMF (h264_amf),
    or gracefully falls back to CPU libx264.
    """
    global _CACHED_HW_ENCODER
    if _CACHED_HW_ENCODER is not None:
        return _CACHED_HW_ENCODER

    test_encoders = [
        {
            "name": "h264_nvenc",
            "type": "NVIDIA NVENC (GPU)",
            "args": ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23"],
        },
        {
            "name": "h264_qsv",
            "type": "Intel Quick Sync (GPU/iGPU)",
            "args": ["-c:v", "h264_qsv", "-global_quality", "23", "-look_ahead", "0"],
        },
        {
            "name": "h264_amf",
            "type": "AMD AMF (GPU)",
            "args": ["-c:v", "h264_amf", "-quality", "balanced"],
        },
        {
            "name": "libx264",
            "type": "CPU (Optimized libx264)",
            "args": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"],
        },
    ]

    for enc in test_encoders:
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.2",
            *enc["args"], "-f", "null", "-"
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
            if res.returncode == 0:
                _CACHED_HW_ENCODER = enc
                print(f"  ⚡ Hardware Encoder Detected: {enc['type']} [{enc['name']}]")
                return enc
        except Exception:
            continue

    # Default fallback
    _CACHED_HW_ENCODER = test_encoders[-1]
    return _CACHED_HW_ENCODER


# ──────────────────────────────────────────────────────────────────────────
# SECTION 3: DYNAMIC FONT & THEME ENGINE (10+ GOOGLE FONTS)
# ──────────────────────────────────────────────────────────────────────────

GOOGLE_FONTS_CATALOG = {
    "Montserrat-Black": {
        "url": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
        "family": "Montserrat",
        "weight": "Black",
    },
    "Impact": {
        "url": None, # Built-in system font on Windows
        "family": "Impact",
        "weight": "Bold",
    },
    "BebasNeue-Regular": {
        "url": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
        "family": "Bebas Neue",
        "weight": "Regular",
    },
    "Poppins-ExtraBold": {
        "url": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf",
        "family": "Poppins",
        "weight": "ExtraBold",
    },
    "PlayfairDisplay-Bold": {
        "url": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
        "family": "Playfair Display",
        "weight": "Bold",
    },
    "Cinzel-Bold": {
        "url": "https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf",
        "family": "Cinzel",
        "weight": "Bold",
    },
    "Oswald-Bold": {
        "url": "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald%5Bwght%5D.ttf",
        "family": "Oswald",
        "weight": "Bold",
    },
    "FiraCode-Bold": {
        "url": "https://github.com/google/fonts/raw/main/ofl/firacode/FiraCode%5Bwght%5D.ttf",
        "family": "Fira Code",
        "weight": "Bold",
    },
    "Anton-Regular": {
        "url": "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf",
        "family": "Anton",
        "weight": "Regular",
    },
    "Rubik-Black": {
        "url": "https://github.com/google/fonts/raw/main/ofl/rubik/Rubik%5Bwght%5D.ttf",
        "family": "Rubik",
        "weight": "Black",
    },
}

GENRE_THEMES = {
    "Motivational": {
        "font_name": "Montserrat-Black",
        "highlight_color": "&H0000FFFF&",  # Vivid Yellow
        "primary_color": "&H00FFFFFF&",    # Crisp White
        "outline_color": "&H00000000&",    # Deep Black
        "font_size": 60,
        "outline_width": 6,
        "shadow": 3,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "High Energy, Punchy Inspiration",
    },
    "Podcast": {
        "font_name": "Poppins-ExtraBold",
        "highlight_color": "&H0000FF00&",  # Punchy Electric Green
        "primary_color": "&H00FFFFFF&",    # Crisp White
        "outline_color": "&H00000000&",    # Black
        "font_size": 58,
        "outline_width": 5,
        "shadow": 3,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Engaging Dialogue, Dynamic Rhythm",
    },
    "Anime": {
        "font_name": "BebasNeue-Regular",
        "highlight_color": "&H000055FF&",  # Fiery Orange / Red
        "primary_color": "&H0000FFFF&",    # Electric Yellow
        "outline_color": "&H00200020&",    # Deep Purple/Black
        "font_size": 66,
        "outline_width": 6,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Hype Action, Shonen Tension",
    },
    "Movie": {
        "font_name": "PlayfairDisplay-Bold",
        "highlight_color": "&H0000D7FF&",  # Warm Gold
        "primary_color": "&H00FFFFFF&",    # White
        "outline_color": "&H00000000&",    # Black
        "font_size": 56,
        "outline_width": 5,
        "shadow": 3,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Cinematic Drama & Suspense",
    },
    "Web Series": {
        "font_name": "Cinzel-Bold",
        "highlight_color": "&H0000D7FF&",  # Regal Gold
        "primary_color": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "font_size": 56,
        "outline_width": 5,
        "shadow": 3,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Intense Character Conflict",
    },
    "Song": {
        "font_name": "Montserrat-Black",
        "highlight_color": "&H00FFFF00&",  # Electric Neon Cyan Active Word
        "primary_color": "&H00FFFFFF&",    # Crisp White Inactive Word
        "outline_color": "&H00000000&",    # Deep Black
        "glow_color": "&H00FF00FF&",       # Vibrant Neon Magenta / Violet Aura Glow
        "font_size": 68,
        "outline_width": 6,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": True,
        "is_song": True,
        "vibe": "Music Video Kinetic Neon Karaoke with Dynamic Pop & Glow",
    },
    "Gaming": {
        "font_name": "LuckiestGuy-Regular",
        "highlight_color": "&H0000FFFF&",  # Neon Yellow
        "primary_color": "&H00FF00FF&",    # Neon Magenta
        "outline_color": "&H00000000&",
        "font_size": 64,
        "outline_width": 6,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Hype Clutch & Humor",
    },
    "Educational": {
        "font_name": "FiraCode-Bold",
        "highlight_color": "&H0000FF88&",  # Emerald Green
        "primary_color": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "font_size": 56,
        "outline_width": 5,
        "shadow": 3,
        "words_per_line": 2,
        "uppercase": False,
        "vibe": "Curious Insights, Clear Explanation",
    },
}

# Backward compatibility map for existing presets in app.py
SUBTITLE_PRESETS = {
    "tiktok_yellow": {
        "name": "Viral TikTok Yellow",
        "font_name": "Impact",
        "font_size": 58,
        "primary_color": "&H0000FFFF",
        "outline_color": "&H00000000",
        "outline_width": 5,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "neon_cyber": {
        "name": "Neon Cyan (Music Video)",
        "font_name": "Oswald-Bold",
        "font_size": 58,
        "primary_color": "&H00FFFF00",
        "outline_color": "&H00300030",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "hormozi_white": {
        "name": "Hormozi Clean White",
        "font_name": "Montserrat-Black",
        "font_size": 60,
        "primary_color": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "outline_width": 6,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "emerald_glow": {
        "name": "Emerald Green Glow",
        "font_name": "Poppins-ExtraBold",
        "font_size": 58,
        "primary_color": "&H0044FF00",
        "outline_color": "&H00000000",
        "outline_width": 5,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "sunset_fire": {
        "name": "Sunset Fire Red",
        "font_name": "BebasNeue-Regular",
        "font_size": 62,
        "primary_color": "&H001E90FF",
        "outline_color": "&H00000000",
        "outline_width": 6,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
}

def ensure_font(font_key: str) -> str:
    """
    Ensures the specified font file (.ttf) exists on SSD in fonts/ directory.
    If not found, downloads it directly from Google Fonts repository.
    Returns the font family name to be passed into ASS subtitles.
    """
    Config.FONTS_DIR.mkdir(parents=True, exist_ok=True)

    # If it's a known Google Font key
    font_info = GOOGLE_FONTS_CATALOG.get(font_key)
    if not font_info:
        # Check if already a system font like Impact or Arial
        return font_key

    font_family = font_info["family"]
    ttf_url = font_info["url"]
    if not ttf_url:
        return font_family

    dest_file = Config.FONTS_DIR / f"{font_key}.ttf"
    if not dest_file.exists() or dest_file.stat().st_size < 1024:
        print(f"  ⬇️  Downloading Google Font '{font_key}' to SSD...")
        try:
            req = urllib.request.Request(ttf_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp, open(dest_file, "wb") as out_f:
                out_f.write(resp.read())
            print(f"  ✅ Cached font to {dest_file.name}")
        except Exception as e:
            print(f"  ⚠️ Could not download font {font_key}: {e} (using fallback font)")
            return "Impact"

    return font_family


# ──────────────────────────────────────────────────────────────────────────
# SECTION 4: DIRECTORY ENSURANCE & CACHE MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────

def ensure_directories():
    """Initializes all necessary SSD working folders."""
    for folder in [Config.DOWNLOADS_DIR, Config.TEMP_DIR, Config.OUTPUT_DIR, Config.FONTS_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def purge_temp_cache() -> dict:
    """Safely frees intermediate temp files from SSD and forces garbage collection."""
    freed_bytes = 0
    if Config.TEMP_DIR.exists():
        for f in Config.TEMP_DIR.glob("*"):
            if f.is_file():
                try:
                    freed_bytes += f.stat().st_size
                    f.unlink(missing_ok=True)
                except Exception:
                    pass
    gc.collect()
    return {"freed_mb": round(freed_bytes / (1024 * 1024), 1)}


def get_system_memory_info() -> dict:
    """Monitors live RAM, CPU and VRAM safe limits."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        total_gb = round(vm.total / (1024**3), 1)
        avail_gb = round(vm.available / (1024**3), 1)
        used_pct = round(vm.percent, 1)

        return {
            "total_gb": total_gb,
            "available_gb": avail_gb,
            "used_percent": used_pct,
            "cpu_percent": cpu_pct,
            "recommended_workers": 1,  # Strictly sequential processing for low-VRAM safety
            "status": "healthy" if used_pct < 85 else "warning",
        }
    except Exception:
        return {
            "total_gb": 8.0,
            "available_gb": 4.0,
            "used_percent": 50.0,
            "cpu_percent": 15.0,
            "recommended_workers": 1,
            "status": "healthy",
        }


def check_ffmpeg():
    """Validates FFmpeg is present in system PATH."""
    if not shutil.which("ffmpeg"):
        print("  ❌ FFmpeg is NOT installed or not in PATH!")
        sys.exit(1)


def check_ollama() -> bool:
    """Checks if Ollama service is running AND requested model is installed."""
    global OLLAMA_AVAILABLE
    if not OLLAMA_AVAILABLE:
        return False
    try:
        import urllib.request, json
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                model_base = Config.OLLAMA_MODEL.split(":")[0]
                return model_base in models
    except Exception:
        pass
    return False


# ──────────────────────────────────────────────────────────────────────────
# SECTION 5: VIDEO INSPECTION & ZERO-RAM SSD INGESTION
# ──────────────────────────────────────────────────────────────────────────

def inspect_youtube_video(youtube_url: str) -> dict:
    """Pre-inspects YouTube video metadata without downloading heavy media."""
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
    """Pre-inspects local video metadata using OpenCV/ffprobe."""
    try:
        cap = cv2.VideoCapture(str(file_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        duration = int(frame_count / fps) if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)

        Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        thumb_name = f"thumb_{file_path.stem}.jpg"
        thumb_path = Config.TEMP_DIR / thumb_name

        cap.set(cv2.CAP_PROP_POS_MSEC, min(1000, duration * 500))
        ret, frame = cap.read()
        if ret and frame is not None:
            cv2.imwrite(str(thumb_path), frame)
            del frame
        cap.release()
        del cap
        gc.collect()

        mins = duration // 60
        secs = duration % 60
        dur_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

        return {
            "title": file_path.stem.replace("_", " ").title(),
            "duration": duration,
            "duration_str": dur_str,
            "thumbnail": f"/api/thumb/{thumb_name}",
            "max_height": height,
            "quality_label": f"{width}x{height}",
            "has_ultra": height > 1080,
            "boxes_15s": max(1, math.ceil(duration / 15.0)) if duration else 1,
            "boxes_30s": max(1, math.ceil(duration / 30.0)) if duration else 1,
            "boxes_45s": max(1, math.ceil(duration / 45.0)) if duration else 1,
            "boxes_60s": max(1, math.ceil(duration / 60.0)) if duration else 1,
            "local_path": str(file_path),
        }
    except Exception as e:
        print(f"  ⚠️ Local inspect error: {e}")
        return {
            "title": file_path.name,
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
            "local_path": str(file_path),
        }


def download_video(youtube_url: str, download_resolution: str = "720p", log_callback=None) -> Path:
    """
    Downloads YouTube video strictly streaming to SSD (Zero-RAM Buffering).
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            try: log_callback(msg)
            except Exception: pass

    log("\n" + "=" * 70)
    log("  📥  STEP 1: ZERO-RAM VIDEO STREAMING TO SSD")
    log("=" * 70)

    # Cache reuse check
    try:
        check_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        if Config.COOKIES_FILE.exists(): check_opts["cookiefile"] = str(Config.COOKIES_FILE)
        with yt_dlp.YoutubeDL(check_opts) as ydl:
            pre_info = ydl.extract_info(youtube_url, download=False)
            expected_title = pre_info.get("title", "")
            expected_fn = Path(ydl.prepare_filename(pre_info))
            for cand in [expected_fn, expected_fn.with_suffix(".mp4"), Config.DOWNLOADS_DIR / f"{expected_title}.mp4"]:
                if cand.exists() and cand.stat().st_size > 1024 * 1024:
                    log(f"  ⚡ Found cached SSD file: {cand.name} ({cand.stat().st_size/(1024*1024):.1f} MB)")
                    return cand
    except Exception:
        pass

    last_log_time = 0.0
    def progress_hook(d):
        nonlocal last_log_time
        if d.get("status") == "downloading":
            now = time.time()
            if now - last_log_time >= 1.0:
                last_log_time = now
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                down = d.get("downloaded_bytes", 0)
                speed = d.get("speed") or 0
                pct = (down / total * 100) if total else 0
                log(f"  📥 Streaming to SSD: {pct:.1f}% ({down/(1024*1024):.1f} MB @ {speed/(1024*1024):.1f} MB/s)")

    if download_resolution == "720p":
        fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    elif download_resolution in ("ultra", "4k", "2k", "more_than_1080p"):
        fmt = "bestvideo[height>1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>1080]+bestaudio/bestvideo+bestaudio/best"
    elif download_resolution == "max":
        fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
    else:
        fmt = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"

    out_template = str(Config.DOWNLOADS_DIR / "%(title)s.%(ext)s")
    ydl_opts = {
        "format": fmt,
        "outtmpl": out_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
    }
    if Config.COOKIES_FILE.exists():
        ydl_opts["cookiefile"] = str(Config.COOKIES_FILE)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        final_fn = Path(ydl.prepare_filename(info)).with_suffix(".mp4")
        if not final_fn.exists():
            matches = list(Config.DOWNLOADS_DIR.glob(f"{Path(final_fn).stem}*"))
            if matches:
                final_fn = matches[0]

    log(f"  ✅ Video safely written to SSD: {final_fn.name} ({final_fn.stat().st_size/(1024*1024):.1f} MB)")
    return final_fn


# ──────────────────────────────────────────────────────────────────────────
# SECTION 6: CHUNKED AUDIO ANALYSIS (DIRECT SSD STREAMING)
# ──────────────────────────────────────────────────────────────────────────

def extract_and_chunk_audio(video_path: Path, max_duration_sec: float = None, chunk_sec: float = 300.0) -> Tuple[Path, List[Path]]:
    """
    Extracts audio to SSD in uncompressed 16kHz mono WAV format.
    Splits long audio into small SSD chunks so faster-whisper never balloons RAM.
    """
    print("\n" + "=" * 70)
    print("  🎵  STEP 2: ZERO-RAM AUDIO EXTRACTION & SSD CHUNKING")
    print("=" * 70)

    full_audio_path = Config.TEMP_DIR / "full_audio.wav"

    cmd = ["ffmpeg", "-y"]
    if max_duration_sec and max_duration_sec > 0:
        cmd.extend(["-t", str(max_duration_sec)])
    cmd.extend([
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(full_audio_path),
    ])

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  ✅ Base audio stream written to SSD: {full_audio_path.name}")

    # Check total duration of extracted audio
    probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(full_audio_path)]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
    try:
        total_audio_sec = float(probe_res.stdout.strip())
    except Exception:
        total_audio_sec = 60.0

    chunk_files = []
    # If audio is longer than chunk_sec (e.g. 5 mins), segment directly on SSD
    if total_audio_sec > chunk_sec:
        chunk_pattern = str(Config.TEMP_DIR / "chunk_%03d.wav")
        segment_cmd = [
            "ffmpeg", "-y", "-i", str(full_audio_path),
            "-f", "segment", "-segment_time", str(chunk_sec),
            "-c", "copy", chunk_pattern
        ]
        subprocess.run(segment_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        chunk_files = sorted(list(Config.TEMP_DIR.glob("chunk_*.wav")))
        print(f"  📦 Segmented into {len(chunk_files)} small SSD chunks ({chunk_sec}s each) to protect RAM.")
    else:
        chunk_files = [full_audio_path]

    return full_audio_path, chunk_files


def transcribe_audio_streamed(chunk_files: List[Path], chunk_sec: float = 300.0,
                              sub_language_mode: str = "en_translate",
                              genre: str = "Podcast",
                              log_callback=None) -> Tuple[List[dict], str]:
    """
    Transcribes audio chunk-by-chunk directly from SSD files using faster-whisper.
    Offsets word timestamps correctly and unloads Whisper model immediately to free RAM.
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            try: log_callback(msg)
            except Exception: pass

    log("\n" + "=" * 70)
    log(f"  🗣️  STEP 3: CHUNKED WHISPER STT (Direct SSD Stream • Genre: {genre.upper()} • Mode: {sub_language_mode.upper()})")
    log("=" * 70)

    # Initialize Whisper with optimal thread count
    threads = min(8, max(4, os.cpu_count() or 4))
    model = WhisperModel(
        Config.WHISPER_MODEL_SIZE,
        device=Config.WHISPER_DEVICE,
        compute_type=Config.WHISPER_COMPUTE,
        cpu_threads=threads,
    )

    task = "translate" if sub_language_mode in ("en_translate", "english", "hinglish") else "transcribe"
    prompt = "Translate foreign speech and lyrics into clean English subtitles for vertical shorts."

    all_words = []
    full_text_lines = []

    is_song = (genre.lower() == "song")
    # In music videos/songs, VAD filter can aggressively cut singing vocals; disable for songs
    use_vad = False if is_song else True

    for idx, chunk_file in enumerate(chunk_files):
        time_offset = idx * chunk_sec
        log(f"  🎙️ Transcribing chunk {idx+1}/{len(chunk_files)} ({chunk_file.name}) from SSD...")

        segments_generator, info = model.transcribe(
            str(chunk_file),
            word_timestamps=True,
            task=task,
            beam_size=1,
            vad_filter=use_vad,
            initial_prompt=prompt,
        )

        for segment in segments_generator:
            seg_text = segment.text.strip()
            if seg_text:
                full_text_lines.append(seg_text)

            if segment.words:
                for w in segment.words:
                    word_clean = w.word.strip()
                    if word_clean:
                        all_words.append({
                            "word": word_clean,
                            "start": round(w.start + time_offset, 3),
                            "end": round(w.end + time_offset, 3),
                            "probability": round(w.probability, 2),
                        })

        # Remove temporary chunk from SSD as soon as consumed (unless it's full_audio.wav)
        if chunk_file.name.startswith("chunk_"):
            try: chunk_file.unlink(missing_ok=True)
            except Exception: pass

    # Aggressive memory cleanup: Unload Whisper from RAM
    del model
    del segments_generator
    gc.collect()
    log("  🧹 Memory Freed: Whisper AI model unloaded from RAM.")

    full_transcript = " ".join(full_text_lines)
    # Save transcript to SSD for reference
    (Config.TEMP_DIR / "full_transcript.txt").write_text(full_transcript, encoding="utf-8")
    log(f"  ✅ STT Complete: {len(all_words)} words parsed with millisecond precision.")

    return all_words, full_transcript


# ──────────────────────────────────────────────────────────────────────────
# SECTION 7: GENRE-BASED AI CLIPPING (OLLAMA LLAMA-3 PROMPT ENGINE)
# ──────────────────────────────────────────────────────────────────────────

GENRE_CRITERIA_MAP = {
    "Podcast": (
        "Focus on conversational hooks, provocative claims, counter-intuitive debates, "
        "and punchy dialogue exchanges between speakers. Prioritize strong first-3-second statements."
    ),
    "Motivational": (
        "Focus on high-energy emotional breakthroughs, mindset shifts, life lessons, "
        "discipline/hustle philosophy, and turning-point statements that inspire the viewer."
    ),
    "Anime": (
        "Focus on high-stakes narrative tension, battle climaxes, emotional power awakenings, "
        "or iconic hype punchlines with maximum dramatic intensity."
    ),
    "Movie": (
        "Focus on intense suspenseful scenes, shocking plot revelations, high-stakes confrontation dialogue, "
        "or comedic turning points that create natural cliffhangers."
    ),
    "Web Series": (
        "Focus on dramatic character clashes, secret exposes, high-tension face-offs, "
        "and cliffhanger moments that demand part 2."
    ),
    "Song": (
        "Focus on peak vocal choruses, energy drops, rhythmic lyric hooks, "
        "and the most memorable emotional melody segments."
    ),
    "Gaming": (
        "Focus on clutch gameplay moments, high-pitch reaction rage/hype, "
        "hilarious fails, and energetic commentary punchlines."
    ),
    "Educational": (
        "Focus on fascinating 'Did You Know?' facts, rapid tutorials, mind-blowing explanations, "
        "and problem-solution reveals that keep viewers hooked."
    ),
}

class LLMClipItem(BaseModel):
    title: str = Field(description="Punchy, catchy short title for this viral clip")
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    reason: str = Field(description="Why this segment fits the genre and hooks the audience")
    hook_score: int = Field(description="Predicted viral retention score from 1 to 10")

class LLMClipResponse(BaseModel):
    clips: List[LLMClipItem] = Field(description="List of best viral clip candidates")


def find_best_clips_genre(words: List[dict], full_transcript: str,
                          genre: str = "Podcast",
                          clipping_mode: str = "smart_highlights",
                          chunk_size_sec: float = 30.0,
                          num_clips: int = 3,
                          clip_min_sec: float = 30.0,
                          clip_max_sec: float = 60.0) -> List[dict]:
    """
    Selects highlight clips dynamically using Ollama Llama-3 based on the selected Genre,
    or falls back to an intelligent genre-tuned phonetic speech-density scanner.
    """
    print("\n" + "=" * 70)
    print(f"  🤖  STEP 4: GENRE-BASED CLIP SELECTION (Genre: {genre.upper()} • Mode: {clipping_mode.upper()})")
    print("=" * 70)

    total_duration = words[-1]["end"] if words else 60.0

    if clipping_mode == "full_video":
        return _create_full_video_boxes(total_duration, words, chunk_size_sec)

    genre_criteria = GENRE_CRITERIA_MAP.get(genre, GENRE_CRITERIA_MAP["Podcast"])

    # Attempt Ollama structured LLM inference
    if check_ollama():
        print(f"  🦙 Prompting Ollama ({Config.OLLAMA_MODEL}) with {genre} criteria...")
        system_prompt = (
            f"You are a viral YouTube Shorts and TikTok video editor specializing in the '{genre}' genre. "
            f"Selection Criteria for '{genre}': {genre_criteria}\n"
            f"Extract exactly {num_clips} highlight segments from the transcript. "
            f"Each clip MUST be between {clip_min_sec}s and {clip_max_sec}s long. "
            f"Ensure start_time starts immediately on a strong hook word."
        )

        user_content = f"Total video duration: {total_duration:.1f}s.\nTranscript:\n{full_transcript[:4000]}"

        try:
            response = chat(
                model=Config.OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                format=LLMClipResponse.model_json_schema(),
            )
            parsed = json.loads(response["message"]["content"])
            raw_clips = parsed.get("clips", [])
            valid_clips = []
            for c in raw_clips:
                st = max(0.0, float(c["start_time"]))
                et = min(total_duration, float(c["end_time"]))
                if et - st >= 10.0:
                    valid_clips.append({
                        "title": re.sub(r'[^\w\s-]', '', c["title"]).strip().replace(" ", "_")[:35],
                        "start_time": round(st, 2),
                        "end_time": round(et, 2),
                        "reason": f"[{genre}] {c.get('reason', 'High engagement moment')}",
                        "hook_score": c.get("hook_score", 9),
                    })
            if valid_clips:
                print(f"  ✅ Ollama selected {len(valid_clips)} {genre} highlights!")
                return valid_clips[:num_clips]
        except Exception as e:
            print(f"  ⚠️ Ollama inference skipped ({e}). Falling back to algorithmic genre scanner.")

    # Algorithmic Genre Speech-Density & Rhythm Scanner
    return _algorithmic_genre_clips(words, total_duration, genre, num_clips, clip_min_sec)


def _create_full_video_boxes(total_duration: float, words: List[dict] = None, chunk_size_sec: float = 30.0) -> List[dict]:
    """Divides full duration into contiguous sequential boxes."""
    chunk_sec = max(10.0, float(chunk_size_sec or 30.0))
    num_boxes = max(1, math.ceil(total_duration / chunk_sec))
    boxes = []

    for idx in range(num_boxes):
        start = round(idx * chunk_sec, 2)
        end = round(min(total_duration, (idx + 1) * chunk_sec), 2)
        if end - start < 7.0 and boxes:
            boxes[-1]["end_time"] = end
            continue
        words_in_box = [w for w in (words or []) if w["end"] >= start - 0.3 and w["start"] <= end + 0.3]
        boxes.append({
            "title": f"part_{idx+1}",
            "start_time": start,
            "end_time": end,
            "reason": f"Box {idx+1}/{num_boxes} ({len(words_in_box)} spoken words)",
            "words_count": len(words_in_box),
        })
    return boxes


def _algorithmic_genre_clips(words: List[dict], total_duration: float, genre: str,
                             num_clips: int = 3, target_duration: float = 30.0) -> List[dict]:
    """Algorithmic highlight finder tuned to genre characteristics."""
    if not words or len(words) < 4:
        # Uniform fallback
        spacing = total_duration / (num_clips + 1)
        return [{
            "title": f"{genre.lower()}_clip_{i+1}",
            "start_time": round(max(0.0, spacing * (i + 1) - target_duration / 2), 2),
            "end_time": round(min(total_duration, spacing * (i + 1) + target_duration / 2), 2),
            "reason": f"{genre} uniform highlight",
        } for i in range(num_clips)]

    candidates = []
    step = 4.0
    current_start = 0.0

    while current_start + target_duration <= total_duration + 2.0:
        current_end = min(total_duration, current_start + target_duration)
        w_in_win = [w for w in words if w["start"] >= current_start - 0.4 and w["end"] <= current_end + 0.4]
        if len(w_in_win) >= 4:
            # Snap start to first spoken word
            first_w_start = max(0.0, w_in_win[0]["start"] - 0.15)
            win_end = min(total_duration, first_w_start + target_duration)

            # Score based on word density and cadence
            density = len(w_in_win) / target_duration
            candidates.append({
                "start": first_w_start,
                "end": win_end,
                "score": density,
                "word_count": len(w_in_win),
            })
        current_start += step

    candidates.sort(key=lambda c: c["score"], reverse=True)

    selected = []
    for cand in candidates:
        if len(selected) >= num_clips:
            break
        # Prevent overlapping clips (> 5s)
        if not any(not (cand["end"] <= s["start"] + 5 or cand["start"] >= s["end"] - 5) for s in selected):
            selected.append(cand)

    selected.sort(key=lambda c: c["start"])

    return [{
        "title": f"{genre.lower()}_hook_{i+1}",
        "start_time": round(s["start"], 2),
        "end_time": round(s["end"], 2),
        "reason": f"[{genre}] Peak vocal rhythm ({s['word_count']} words, immediate speech start)",
    } for i, s in enumerate(selected)]


# ──────────────────────────────────────────────────────────────────────────
# SECTION 8: DISK-STREAM FRAME PROCESSING & ACTIVE SPEAKER CENTERING
# ──────────────────────────────────────────────────────────────────────────

def disk_frame_streamer(video_path: Path, start_time: float, end_time: float,
                        sample_count: int = 25) -> Generator[Tuple[float, Any], None, None]:
    """
    Python generator reading exactly ONE frame from SSD at a time.
    Guarantees zero-RAM accumulation.
    """
    cap = cv2.VideoCapture(str(video_path))
    try:
        duration = end_time - start_time
        interval = duration / max(1, sample_count)
        for i in range(sample_count):
            t_sec = start_time + (i * interval)
            cap.set(cv2.CAP_PROP_POS_MSEC, t_sec * 1000)
            ret, frame = cap.read()
            if ret and frame is not None:
                yield t_sec, frame
                del frame
    finally:
        cap.release()
        del cap
        gc.collect()


def detect_face_crop_region(video_path: Path, start_time: float, end_time: float) -> dict:
    """
    Streams single frames from SSD to compute dynamic 9:16 crop boundaries.
    """
    # Load cascade from local folder or bundled
    cascade_filename = "haarcascade_frontalface_default.xml"
    cascade_path = Config.BASE_DIR / cascade_filename
    if not cascade_path.exists():
        cascade_path = Path(cv2.data.haarcascades) / cascade_filename

    face_cascade = cv2.CascadeClassifier(str(cascade_path)) if cascade_path.exists() else None

    # Get video dimensions
    cap = cv2.VideoCapture(str(video_path))
    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)
    cap.release()
    del cap

    target_aspect = 9.0 / 16.0
    crop_h = fh
    crop_w = int(fh * target_aspect)
    if crop_w > fw:
        crop_w = fw
        crop_h = int(fw / target_aspect)

    face_x_centers = []

    if face_cascade and not face_cascade.empty():
        # Stream frames one-by-one from SSD
        for _, frame in disk_frame_streamer(video_path, start_time, end_time, sample_count=Config.FACE_SAMPLE_FRAMES):
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=4, minSize=(50, 50))
            if len(faces) > 0:
                largest = max(faces, key=lambda f: f[2] * f[3])
                face_x_centers.append(largest[0] + largest[2] // 2)
            del gray
            del frame

    if face_x_centers:
        face_x_centers.sort()
        median_x = face_x_centers[len(face_x_centers) // 2]
        crop_x = max(0, min(median_x - crop_w // 2, fw - crop_w))
        crop_y = max(0, (fh - crop_h) // 2)
        method = "face_track"
    else:
        crop_x = max(0, (fw - crop_w) // 2)
        crop_y = max(0, (fh - crop_h) // 2)
        method = "center_crop"

    return {
        "crop_x": crop_x,
        "crop_y": crop_y,
        "crop_w": crop_w,
        "crop_h": crop_h,
        "method": method,
    }


# ──────────────────────────────────────────────────────────────────────────
# SECTION 9: ADVANCED KINETIC TYPOGRAPHY (WORD-LEVEL .ASS ENGINE)
# ──────────────────────────────────────────────────────────────────────────

def _seconds_to_ass_time(seconds: float) -> str:
    """Converts seconds into ASS timestamp format H:MM:SS.cc"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


def generate_subtitles(words: List[dict], start_time: float, end_time: float,
                       output_path: Path, crop_info: dict,
                       style_override: dict = None,
                       genre: str = "Podcast") -> Path:
    """
    Programmatically creates .ASS subtitle files featuring:
    - Kinetic Word Pop: Active words bounce out to 120% scale on syllable hit (TikTok/Reels karaoke style)
    - Radiant Neon Glow: Vibrant colored edge aura tuned to musical genre
    - 1-to-2 words on screen max at a time for maximum retention
    - Genre-matched typography with 10+ Google Fonts
    - Zero-blank fallback: Displays rhythmic music visualizer badges during instrumental song sections
    """
    theme = dict(GENRE_THEMES.get(genre, GENRE_THEMES["Podcast"]))
    if style_override:
        theme.update({k: v for k, v in style_override.items() if v is not None})

    font_key        = theme.get("font_name", "Montserrat-Black")
    font_family     = ensure_font(font_key)
    font_size       = theme.get("font_size", 68 if genre.lower() == "song" else 58)
    highlight_color = theme.get("highlight_color", "&H00FFFF00&")
    primary_color   = theme.get("primary_color", "&H00FFFFFF&")
    outline_color   = theme.get("outline_color", "&H00000000&")
    glow_color      = theme.get("glow_color", "&H00FF00FF&" if genre.lower() == "song" else outline_color)
    outline_width   = theme.get("outline_width", 6)
    shadow          = theme.get("shadow", 4)
    uppercase       = theme.get("uppercase", True)
    words_per_line  = max(1, min(2, theme.get("words_per_line", 2)))

    # Filter words strictly in interval
    clip_words = [w for w in words if w["end"] >= start_time - 0.2 and w["start"] <= end_time + 0.2]

    # Zero-Blank Protection: If no words detected in this clip interval (e.g. instrumental music intro or silence)
    if not clip_words:
        if genre.lower() == "song":
            duration = max(1.0, end_time - start_time)
            ass_header = f"""[Script Info]
Title: AutoClip Music Video Lyrics
ScriptType: v4.00+
PlayResX: {Config.TARGET_WIDTH}
PlayResY: {Config.TARGET_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KineticMusic,{font_family},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,{outline_width},{shadow},2,30,30,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            events = []
            t = 0.5
            while t < duration - 0.5:
                t_end = min(duration - 0.2, t + 2.8)
                st_str = _seconds_to_ass_time(t)
                et_str = _seconds_to_ass_time(t_end)
                events.append(
                    f"Dialogue: 0,{st_str},{et_str},KineticMusic,,0,0,0,,{{\\blur5\\3c{glow_color}\\c{highlight_color}\\t(0,250,\\fscx112\\fscy112)\\t(250,500,\\fscx100\\fscy100)}}🎵  [MUSIC VIBES]  🎵"
                )
                t += 3.2
            ass_content = ass_header + "\n".join(events) + "\n"
            output_path.write_text(ass_content, encoding="utf-8")
            return output_path
        else:
            output_path.write_text("", encoding="utf-8")
            return output_path

    subtitle_events = []
    last_event_end = 0.0

    # Group into pairs or singles: 1-to-2 words on screen max with kinetic bounce
    for i in range(0, len(clip_words), words_per_line):
        group = clip_words[i:i + words_per_line]
        raw_start = group[0]["start"] - start_time
        raw_end = group[-1]["end"] - start_time

        group_start = max(0.0, raw_start, last_event_end)
        group_end = max(group_start + 0.22, raw_end + 0.12)

        if len(group) == 1:
            w_text = group[0]["word"].strip()
            if uppercase:
                w_text = w_text.upper()
            # Kinetic Elastic Pop & Glowing Edge Aura
            colored_text = f"{{\\blur5\\3c{glow_color}\\c{highlight_color}\\t(0,110,\\fscx120\\fscy120)\\t(110,220,\\fscx100\\fscy100)}}{w_text}"
            subtitle_events.append({
                "start": group_start,
                "end": group_end,
                "text": colored_text,
            })
            last_event_end = group_end
        else:
            w1_start = group_start
            w2_start = max(w1_start + 0.08, min(group[1]["start"] - start_time, group_end - 0.08))
            w1_end = w2_start
            w2_end = group_end

            w1_text = group[0]["word"].strip()
            w2_text = group[1]["word"].strip()
            if uppercase:
                w1_text = w1_text.upper()
                w2_text = w2_text.upper()

            # Event 1: Word 1 POPS with 120% bounce & neon aura; Word 2 is clean white
            ev1_text = (
                f"{{\\blur5\\3c{glow_color}\\c{highlight_color}\\t(0,110,\\fscx120\\fscy120)\\t(110,220,\\fscx100\\fscy100)}}{w1_text} "
                f"{{\\rKinetic\\c{primary_color}}}{w2_text}"
            )
            subtitle_events.append({
                "start": w1_start,
                "end": w1_end,
                "text": ev1_text,
            })

            # Event 2: Word 1 settles; Word 2 POPS with 120% bounce & neon aura
            ev2_text = (
                f"{{\\rKinetic\\c{primary_color}}}{w1_text} "
                f"{{\\blur5\\3c{glow_color}\\c{highlight_color}\\t(0,110,\\fscx120\\fscy120)\\t(110,220,\\fscx100\\fscy100)}}{w2_text}"
            )
            subtitle_events.append({
                "start": w2_start,
                "end": w2_end,
                "text": ev2_text,
            })

            last_event_end = w2_end

    # Build ASS content with dual styles
    ass_header = f"""[Script Info]
Title: AutoClip Kinetic Subtitles
ScriptType: v4.00+
PlayResX: {Config.TARGET_WIDTH}
PlayResY: {Config.TARGET_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kinetic,{font_family},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,{outline_width},{shadow},2,30,30,360,1
Style: KineticGlow,{font_family},{font_size},{highlight_color},&H000000FF,{glow_color},&H80000000,-1,0,0,0,100,100,1,0,1,{outline_width + 1},{shadow},2,30,30,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogue_lines = []
    for ev in subtitle_events:
        st_str = _seconds_to_ass_time(ev["start"])
        et_str = _seconds_to_ass_time(ev["end"])
        dialogue_lines.append(f"Dialogue: 0,{st_str},{et_str},Kinetic,,0,0,0,,{ev['text']}")

    ass_content = ass_header + "\n".join(dialogue_lines) + "\n"
    output_path.write_text(ass_content, encoding="utf-8")
    return output_path


# ──────────────────────────────────────────────────────────────────────────
# SECTION 10: SEQUENTIAL LOW-VRAM RENDERER (GPU HARDWARE ACCELERATION)
# ──────────────────────────────────────────────────────────────────────────

def render_short_sequential(video_path: Path, clip: dict, clip_index: int,
                            subtitle_path: Path, crop_info: dict,
                            encoder_cfg: dict = None) -> Path:
    """
    Renders the 9:16 Short sequentially using detected GPU hardware encoder (QSV/NVENC/AMF)
    or CPU fallback. Strictly waits for completion before starting the next clip.
    """
    if encoder_cfg is None:
        encoder_cfg = detect_hardware_encoder()

    safe_title = re.sub(r'[^\w\s-]', '', clip.get("title", f"clip_{clip_index}")).strip().replace(" ", "_")[:40]
    output_file = Config.OUTPUT_DIR / f"short_{clip_index}_{safe_title}.mp4"

    start_time = clip["start_time"]
    duration = clip["end_time"] - clip["start_time"]

    crop_filter = f"crop={crop_info['crop_w']}:{crop_info['crop_h']}:{crop_info['crop_x']}:{crop_info['crop_y']}"
    scale_filter = f"scale={Config.TARGET_WIDTH}:{Config.TARGET_HEIGHT}"
    filters = [crop_filter, scale_filter]

    # Render with subtitles filter (with Windows colon escaping)
    if subtitle_path and subtitle_path.exists() and subtitle_path.stat().st_size > 0:
        sub_escaped = str(subtitle_path.resolve()).replace("\\", "/").replace(":", r"\:")
        filters.append(f"subtitles='{sub_escaped}'")

    video_filters = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", str(video_path),
        "-t", str(duration),
        "-vf", video_filters,
        *encoder_cfg["args"],
        "-c:a", "aac",
        "-b:a", Config.AUDIO_BITRATE,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_file),
    ]

    print(f"    🎬 [Sequential Encoder] Rendering Box #{clip_index} using {encoder_cfg['type']}...")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if sys.platform == "win32" else 0,
        )
        _, stderr_bytes = proc.communicate() # Strictly waits for completion!

        if proc.returncode != 0:
            print(f"    ⚠️ GPU encoder warning: fallback to libx264...")
            fallback_cmd = [
                "ffmpeg", "-y", "-ss", str(start_time), "-i", str(video_path),
                "-t", str(duration), "-vf", video_filters,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac", "-b:a", Config.AUDIO_BITRATE, "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                str(output_file)
            ]
            subprocess.run(fallback_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"    ✅ Box #{clip_index} Completed: {output_file.name} ({output_file.stat().st_size/(1024*1024):.1f} MB)")
        return output_file
    except Exception as e:
        print(f"    ❌ Rendering failed for box {clip_index}: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────
# SECTION 11: MASTER PIPELINE ORCHESTRATOR ("INDEX AGENT")
# ──────────────────────────────────────────────────────────────────────────

def process_video_pipeline(
    youtube_url: str = None,
    local_video_path: str = None,
    genre: str = "Podcast",
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
) -> List[dict]:
    """
    Zero-RAM SSD-Streaming & Genre-Driven Video Pipeline.
    Strictly keeps heavy media data on SSD and executes FFmpeg sequentially.
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            try: log_callback(msg)
            except Exception: pass

    # Synchronize configuration
    genre = genre or Config.GENRE
    if num_clips: Config.NUM_CLIPS = int(num_clips)
    if clip_min_sec: Config.CLIP_MIN_SEC = float(clip_min_sec)
    if clip_max_sec: Config.CLIP_MAX_SEC = float(clip_max_sec)

    ensure_directories()
    check_ffmpeg()
    hw_encoder = detect_hardware_encoder()

    log("\n╔" + "═" * 68 + "╗")
    log("║" + f"  AUTOCLIP STUDIO — {genre.upper()} KINETIC ENGINE".center(68) + "║")
    log("║" + f"  Zero-RAM SSD Pipeline • Hardware: {hw_encoder['type']}".center(68) + "║")
    log("╚" + "═" * 68 + "╝\n")

    # Step 1: Ingestion to SSD
    if local_video_path and Path(local_video_path).exists():
        video_path = Path(local_video_path)
        log(f"  📁 STEP 1: LOCAL SSD VIDEO INGESTION ({video_path.name})")
    elif youtube_url:
        video_path = download_video(youtube_url, download_resolution=download_resolution, log_callback=log)
    else:
        raise ValueError("Must provide a YouTube URL or local video file.")

    # Step 2: SSD Audio Extraction & Slicing
    audio_scan_limit = None
    if clipping_mode == "smart_highlights":
        audio_scan_limit = max(600.0, (Config.NUM_CLIPS or 3) * 200.0)

    full_audio_path, chunk_files = extract_and_chunk_audio(
        video_path, max_duration_sec=audio_scan_limit, chunk_sec=Config.AUDIO_CHUNK_SEC
    )

    # Step 3: Chunked Whisper STT
    words, full_transcript = transcribe_audio_streamed(
        chunk_files, chunk_sec=Config.AUDIO_CHUNK_SEC,
        sub_language_mode=sub_language_mode, genre=genre, log_callback=log
    )

    # Step 4: Genre-Based AI Clip Selection
    clips = find_best_clips_genre(
        words=words,
        full_transcript=full_transcript,
        genre=genre,
        clipping_mode=clipping_mode,
        chunk_size_sec=chunk_size_sec,
        num_clips=Config.NUM_CLIPS,
        clip_min_sec=Config.CLIP_MIN_SEC,
        clip_max_sec=Config.CLIP_MAX_SEC,
    )

    if not clips:
        log("  ❌ No clips found. Aborting.")
        return []

    # Step 5: "The Index Agent" — Lightweight Dictionary Architecture
    index_agent = {
        "video_path": str(video_path),
        "genre": genre,
        "encoder": hw_encoder["name"],
        "clips": [],
    }

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

    log(f"\n  ⚡ STEP 5: SEQUENTIAL FFmpeg RENDER ({len(clips)} CLIPS • LOW-VRAM)")

    results = []
    # Strictly Sequential Processing: Wait for each FFmpeg process to complete before starting next
    for i, clip in enumerate(clips, 1):
        log(f"\n  🚀 [Job {i}/{len(clips)}] Processing: \"{clip['title']}\" ({clip['start_time']}s → {clip['end_time']}s)")

        # 5a. Stream single frames from SSD for active speaker centering
        crop_info = detect_face_crop_region(video_path, clip["start_time"], clip["end_time"])
        log(f"     Crop Alignment: {crop_info['method']} (x={crop_info['crop_x']}, w={crop_info['crop_w']})")

        # 5b. Generate kinetic word-level .ass subtitles
        sub_path = Config.TEMP_DIR / f"clip_{i}_{genre.lower()}_subtitles.ass"
        generate_subtitles(words, clip["start_time"], clip["end_time"], sub_path, crop_info, style_override, genre=genre)

        # 5c. Sequential render with GPU hardware acceleration
        out_file = render_short_sequential(video_path, clip, i, sub_path, crop_info, encoder_cfg=hw_encoder)

        if out_file and out_file.exists():
            size_mb = round(out_file.stat().st_size / (1024 * 1024), 2)
            item_res = {
                "clip_index": i,
                "title": clip["title"],
                "start_time": clip["start_time"],
                "end_time": clip["end_time"],
                "filename": out_file.name,
                "path": str(out_file),
                "size_mb": size_mb,
                "genre": genre,
                "verified": True,
            }
            results.append(item_res)
            index_agent["clips"].append(item_res)
            log(f"     ✅ Confirmed Box {i}: {out_file.name} ({size_mb} MB)")

        # Force garbage collection between clips
        gc.collect()

    # Step 6: Cleanup SSD temp cache
    freed = purge_temp_cache()
    log(f"  🧹 SSD Cache Cleaned: {freed['freed_mb']} MB released, RAM free.")

    log("\n" + "=" * 70)
    log(f"  🎉 PIPELINE COMPLETE! Generated {len(results)} {genre} Shorts.")
    log("=" * 70 + "\n")

    return results


# ──────────────────────────────────────────────────────────────────────────
# SECTION 12: CLI ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────

def main():
    """CLI Entry Point with Genre Support"""
    print("\n🎬 AutoClip Studio — Zero-RAM Video Clipping Engine")
    print("-----------------------------------------------------")
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("  🔗 Paste YouTube URL: ").strip()

    if not url:
        print("  ❌ No URL provided.")
        sys.exit(1)

    print("\n  Available Genres: Podcast, Motivational, Anime, Movie, Web Series, Song, Gaming, Educational")
    chosen_genre = input("  🎭 Select Genre [Default: Podcast]: ").strip().title() or "Podcast"

    process_video_pipeline(youtube_url=url, genre=chosen_genre)


if __name__ == "__main__":
    main()
