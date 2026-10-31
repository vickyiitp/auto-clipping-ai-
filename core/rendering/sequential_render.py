"""
Sequential Low-VRAM Renderer.
Renders 9:16 Shorts sequentially using hardware-accelerated GPU transcoding
with self-healing fallback tiers to CPU and safe crop filters.
"""

import re
import subprocess
from pathlib import Path

from core.config import Config
from core.biomimetic.memory_governor import LaminarMemoryGovernor
from core.biomimetic.route_mesh import ROUTE_MESH
from core.rendering.hw_detector import detect_hardware_encoder


def render_short_sequential(video_path: Path, clip: dict, clip_index: int,
                            subtitle_path: Path, crop_info: dict,
                            encoder_cfg: dict = None,
                            video_title: str = None) -> Path:
    """
    Renders the 9:16 Short sequentially using detected GPU hardware encoder (QSV/NVENC/AMF)
    or CPU fallback. Strictly waits for completion before starting the next clip.
    """
    if encoder_cfg is None:
        encoder_cfg = detect_hardware_encoder()

    raw_title = video_title or (video_path.stem if video_path else f"video_{clip_index}")
    clean_title = re.sub(r'[\\/*?:"<>|]', '', str(raw_title)).strip()
    clean_title = re.sub(r'\s+', ' ', clean_title)[:80].strip()
    if not clean_title:
        clean_title = "Video"

    output_file = Config.OUTPUT_DIR / f"{clean_title} - Part {clip_index}.mp4"

    start_time = clip["start_time"]
    duration = clip["end_time"] - clip["start_time"]
    crop_x_val = crop_info.get("crop_expr") if crop_info.get("crop_expr") is not None else crop_info["crop_x"]
    crop_filter = f"crop={crop_info['crop_w']}:{crop_info['crop_h']}:'{crop_x_val}':{crop_info['crop_y']}"
    scale_filter = f"scale={Config.TARGET_WIDTH}:{Config.TARGET_HEIGHT}"
    filters = [crop_filter, scale_filter]

    # Render with subtitles filter (with Windows colon escaping and explicit SSD fontsdir)
    if subtitle_path and subtitle_path.exists() and subtitle_path.stat().st_size > 0:
        sub_escaped = str(subtitle_path.resolve()).replace("\\", "/").replace(":", r"\:")
        fonts_dir_escaped = str(Config.FONTS_DIR.resolve()).replace("\\", "/").replace(":", r"\:")
        filters.append(f"subtitles='{sub_escaped}':fontsdir='{fonts_dir_escaped}'")

    video_filters = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-hwaccel", "auto",
        "-filter_threads", "4",
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

    def _tier1_gpu_render():
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        _, stderr_bytes = proc.communicate()
        if proc.returncode != 0:
            err = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else 'unknown'
            raise RuntimeError(f"GPU hardware encoder failed (code {proc.returncode}): {err[:80]}")
        return output_file

    def _tier2_cpu_render():
        fallback_cmd = [
            "ffmpeg", "-y", "-hwaccel", "auto", "-filter_threads", "4",
            "-ss", str(start_time), "-i", str(video_path),
            "-t", str(duration), "-vf", video_filters,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", Config.AUDIO_BITRATE, "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output_file)
        ]
        proc = subprocess.Popen(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        _, stderr_bytes = proc.communicate()
        if proc.returncode != 0:
            err = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else 'unknown'
            raise RuntimeError(f"CPU libx264 render failed (code {proc.returncode}): {err[:80]}")
        return output_file

    def _tier3_safe_crop_render():
        safe_filters = f"{crop_filter},{scale_filter}"
        safe_cmd = [
            "ffmpeg", "-y", "-hwaccel", "auto",
            "-ss", str(start_time), "-i", str(video_path),
            "-t", str(duration), "-vf", safe_filters,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24",
            "-c:a", "aac", "-b:a", Config.AUDIO_BITRATE, "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output_file)
        ]
        subprocess.run(safe_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_file

    LaminarMemoryGovernor.guard_memory_pressure()
    print(f"    🎬 [Sequential Encoder] Rendering Box #{clip_index} using {encoder_cfg['type']}...")
    try:
        res = ROUTE_MESH.execute("R6_HW_TRANSCODE", [
            (f"Tier 1: {encoder_cfg['type']}", _tier1_gpu_render),
            ("Tier 2: Multi-Threaded libx264 CPU", _tier2_cpu_render),
            ("Tier 3: Safe Video Crop Passthrough", _tier3_safe_crop_render),
        ], log_callback=print)
        if res and res.exists():
            print(f"    ✅ Box #{clip_index} Completed: {output_file.name} ({output_file.stat().st_size/(1024*1024):.1f} MB)")
            return res
        return None
    except Exception as e:
        print(f"    ❌ Rendering failed for box {clip_index}: {e}")
        return None

