import re
import time
import math
import gc
from pathlib import Path
from typing import Dict, Any, Optional
import yt_dlp
import cv2

from core.config import Config
from core.biomimetic import ROUTE_MESH

def inspect_youtube_info(youtube_url: str) -> Dict[str, Any]:
    """Inspects video metadata (title, duration, quality) without downloading."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if Config.COOKIES_FILE.exists():
        opts["cookiefile"] = str(Config.COOKIES_FILE)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            dur = info.get("duration", 0)
            mins = dur // 60
            secs = dur % 60
            dur_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

            formats = info.get("formats", [])
            max_height = 0
            has_ultra = False
            for f in formats:
                h = f.get("height") or 0
                if h > max_height:
                    max_height = h
                if h > 1080:
                    has_ultra = True

            quality_label = f"{max_height}p" if max_height else "1080p"
            thumb = info.get("thumbnail") or ""

            return {
                "title": info.get("title", "Unknown Title"),
                "duration": dur,
                "duration_str": dur_str,
                "thumbnail": thumb,
                "max_height": max_height,
                "quality_label": quality_label,
                "has_ultra": has_ultra,
                "boxes_15s": max(1, math.ceil(dur / 15.0)) if dur else 1,
                "boxes_30s": max(1, math.ceil(dur / 30.0)) if dur else 1,
                "boxes_45s": max(1, math.ceil(dur / 45.0)) if dur else 1,
                "boxes_60s": max(1, math.ceil(dur / 60.0)) if dur else 1,
            }
    except Exception as e:
        print(f"  ⚠️ Fast inspect error: {e}")
        return {
            "title": "YouTube Video",
            "duration": 0,
            "duration_str": "Unknown",
            "thumbnail": "",
            "max_height": 1080,
            "quality_label": "1080p",
            "has_ultra": False,
            "boxes_15s": 1,
            "boxes_30s": 1,
            "boxes_45s": 1,
            "boxes_60s": 1,
        }

inspect_youtube_video = inspect_youtube_info

def download_video(youtube_url: str, download_resolution: str = "720p", log_callback=None) -> Path:
    """Downloads YouTube video strictly streaming to SSD (Zero-RAM Buffering)."""
    def log(msg: str):
        print(msg)
        if log_callback:
            try: log_callback(msg)
            except Exception: pass

    log("\n" + "=" * 70)
    log("  📥  STEP 1: ZERO-RAM VIDEO STREAMING TO SSD")
    log("=" * 70)

    # Fast local cache check before network calls
    try:
        vid_id_match = re.search(r'(?:v=|\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})', youtube_url)
        if vid_id_match:
            v_id = vid_id_match.group(1)
            for cand in Config.DOWNLOADS_DIR.glob(f"*{v_id}*"):
                if cand.suffix.lower() in (".mp4", ".mkv", ".webm") and cand.stat().st_size > 1024 * 1024:
                    log(f"  ⚡ Found instant cached SSD file: {cand.name} ({cand.stat().st_size/(1024*1024):.1f} MB)")
                    return cand

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

    def _tier1_split_merge():
        ydl_opts = {
            "format": fmt,
            "outtmpl": out_template,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "concurrent_fragment_downloads": 4,
            "buffersize": 1048576,
            "http_chunk_size": 10485760,
        }
        if Config.COOKIES_FILE.exists(): ydl_opts["cookiefile"] = str(Config.COOKIES_FILE)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            dl_fn = Path(ydl.prepare_filename(info))
            for cand in [dl_fn, dl_fn.with_suffix(".mp4"), Config.DOWNLOADS_DIR / f"{info.get('title', '')}.mp4"]:
                if cand.exists(): return cand
            return dl_fn

    def _tier2_single_container():
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": out_template,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
        }
        if Config.COOKIES_FILE.exists(): ydl_opts["cookiefile"] = str(Config.COOKIES_FILE)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            return Path(ydl.prepare_filename(info))

    def _tier3_cached_fallback():
        files = sorted(list(Config.DOWNLOADS_DIR.glob("*.mp4")), key=lambda f: f.stat().st_mtime, reverse=True)
        if files: return files[0]
        raise RuntimeError("Zero local fallback video streams available.")

    res = ROUTE_MESH.execute("R1_INGESTION", [
        ("Tier 1: 1080p Split-Merge Stream", _tier1_split_merge),
        ("Tier 2: Single Container Stream", _tier2_single_container),
        ("Tier 3: Local Cached Stream", _tier3_cached_fallback),
    ], log_callback=log)

    log(f"  ✅ Video streamed to SSD: {res.name} ({res.stat().st_size/(1024*1024):.1f} MB)")
    return res
