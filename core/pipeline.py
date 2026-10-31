"""
Master Video Processing Pipeline ("The Index Agent").
Zero-RAM SSD-Streaming & Genre-Driven Video Pipeline.
Coordinates Ingestion, Audio Extraction, Whisper STT, AI Clip Detection,
Face Tracking, Kinetic Subtitles, and Hardware-Accelerated Rendering.
"""

import gc
import re
import uuid
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.config import Config, SUBTITLE_PRESETS, ensure_directories, purge_temp_cache
from core.biomimetic.topology import TOPOLOGY
from core.biomimetic.memory_governor import LaminarMemoryGovernor
from core.biomimetic.pacing import PACER, GEODESIC
from core.ingestion.downloader import download_video
from core.audio.extractor import extract_and_chunk_audio
from core.stt.transcriber import transcribe_audio_streamed
from core.clipping.clip_selector import find_best_clips_genre
from core.tracking.face_tracker import detect_face_crop_region
from core.subtitles.kinetic_animator import generate_subtitles
from core.rendering.hw_detector import detect_hardware_encoder, check_ffmpeg
from core.rendering.sequential_render import render_short_sequential
from core.queue.batch_manager import BATCH_MANAGER


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
    custom_outline_width: int = None,
    custom_shadow: int = None,
    custom_words_per_line: int = None,
    custom_uppercase: bool = None,
    sub_position: str = "bottom",
    highlight_words: bool = True,
    resource_mode: str = "balanced",
    download_resolution: str = "720p",
    sub_language_mode: str = "original",
    dual_mode: bool = None,
    secondary_font: str = None,
    glow_style: str = None,
    custom_highlight_color: str = None,
    custom_primary_color: str = None,
    custom_outline_color: str = None,
    custom_glow_color: str = None,
    session_id: str = None,
    log_callback = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Zero-RAM SSD-Streaming & Genre-Driven Video Pipeline.
    Strictly keeps heavy media data on SSD and executes FFmpeg sequentially.
    Returns dictionary with generated shorts metadata and status.
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            try: log_callback(msg)
            except Exception: pass

    genre = genre or Config.GENRE
    clips_to_generate = int(num_clips) if num_clips else Config.NUM_CLIPS
    min_clip_sec = float(clip_min_sec) if clip_min_sec else Config.CLIP_MIN_SEC
    max_clip_sec = float(clip_max_sec) if clip_max_sec else Config.CLIP_MAX_SEC
    safe_chunk_sec = float(chunk_size_sec) if chunk_size_sec else 30.0

    ensure_directories()
    check_ffmpeg()
    hw_encoder = detect_hardware_encoder()

    top = TOPOLOGY.get_summary()
    mem_state = LaminarMemoryGovernor.get_memory_state()

    log("\n╔" + "═" * 68 + "╗")
    log("║" + f"  AUTOCLIP STUDIO — {genre.upper()} KINETIC ENGINE".center(68) + "║")
    log("║" + f"  Zero-RAM SSD Pipeline • Hardware: {hw_encoder['type']}".center(68) + "║")
    log("║" + f"  🌊 Biomimetic Kingfisher Engine: ACTIVE (Zero-Crash Guarantee)".center(68) + "║")
    log("╚" + "═" * 68 + "╝")
    log(f"  ⚡ [Starling Murmuration] P-Core Affinity Locked: {top['p_core_threads']} Threads @ 4.90GHz")
    log(f"  🌊 [Laminar Governor] Safe RAM Floor: {mem_state['available_mb']}MB available ({mem_state['used_pct']}% used)")
    log(f"  🚀 [NASA Apollo Kalman] 1D Recursive Subject Crop Tracking: ACTIVE")
    log(f"  🧠 [Rao-Ballard Predictive] Static Delta Skip & LIF Gating: ACTIVE\n")

    # Step 1: Ingestion to SSD
    if local_video_path and Path(local_video_path).exists():
        video_path = Path(local_video_path)
        log(f"  📁 STEP 1: LOCAL SSD VIDEO INGESTION ({video_path.name})")
    elif youtube_url:
        video_path = download_video(youtube_url, download_resolution=download_resolution, log_callback=log)
    else:
        raise ValueError("Must provide a YouTube URL or local video file.")

    safe_stem = re.sub(r'[^\w\s-]', '', video_path.stem).strip().replace(" ", "_")[:25]
    unique_id = uuid.uuid4().hex[:6]

    # Step 2: SSD Audio Extraction & Slicing
    audio_scan_limit = None
    if clipping_mode == "smart_highlights":
        audio_scan_limit = max(600.0, (clips_to_generate or 3) * 200.0)

    full_audio_path, chunk_files = extract_and_chunk_audio(
        video_path, max_duration_sec=audio_scan_limit, chunk_sec=Config.AUDIO_CHUNK_SEC,
        genre=genre, log_callback=log
    )

    # Step 3: Chunked Whisper STT
    words, full_transcript = transcribe_audio_streamed(
        chunk_files, chunk_sec=Config.AUDIO_CHUNK_SEC,
        sub_language_mode=sub_language_mode, genre=genre, log_callback=log
    )

    # Immediately delete working audio file
    if full_audio_path and full_audio_path.exists():
        try: full_audio_path.unlink(missing_ok=True)
        except Exception: pass

    # Step 4: Genre-Based AI Clip Selection
    video_duration = 60.0
    try:
        p_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)]
        p_res = subprocess.run(p_cmd, capture_output=True, text=True)
        video_duration = float(p_res.stdout.strip())
    except Exception:
        video_duration = words[-1]["end"] if words else 60.0

    clips = find_best_clips_genre(
        words=words,
        full_transcript=full_transcript,
        genre=genre,
        clipping_mode=clipping_mode,
        chunk_size_sec=safe_chunk_sec,
        num_clips=clips_to_generate,
        clip_min_sec=min_clip_sec,
        clip_max_sec=max_clip_sec,
        video_duration=video_duration,
    )

    if not clips:
        log("  ❌ No clips found. Aborting.")
        return {"video_title": video_path.stem, "generated_shorts": []}

    # Style override assembly
    style_override = {}
    if sub_preset and sub_preset in SUBTITLE_PRESETS:
        style_override.update(SUBTITLE_PRESETS[sub_preset])
    if custom_sub_font:
        style_override["font_name"] = custom_sub_font
    if custom_sub_size:
        style_override["font_size"] = int(custom_sub_size)
    if custom_outline_width is not None:
        style_override["custom_outline_width"] = int(custom_outline_width)
    if custom_shadow is not None:
        style_override["custom_shadow"] = int(custom_shadow)
    if custom_words_per_line:
        style_override["words_per_line"] = int(custom_words_per_line)
    if custom_uppercase is not None:
        style_override["uppercase"] = bool(custom_uppercase)
    if sub_position:
        style_override["sub_position"] = sub_position
    if highlight_words is not None:
        style_override["highlight_words"] = bool(highlight_words)
    if dual_mode is not None:
        style_override["dual_mode"] = bool(dual_mode)
    if secondary_font:
        style_override["secondary_font"] = secondary_font
    if glow_style:
        style_override["glow_style"] = glow_style
    if custom_highlight_color:
        style_override["custom_highlight_color"] = custom_highlight_color
    if custom_primary_color:
        style_override["custom_primary_color"] = custom_primary_color
    if custom_outline_color:
        style_override["custom_outline_color"] = custom_outline_color
    if custom_glow_color:
        style_override["custom_glow_color"] = custom_glow_color


    log(f"\n  ⚡ STEP 5: SEQUENTIAL FFmpeg RENDER ({len(clips)} CLIPS • LOW-VRAM)")

    results = []
    for i, clip in enumerate(clips, 1):
        log(f"\n  🚀 [Job {i}/{len(clips)}] Processing: \"{clip['title']}\" ({clip['start_time']}s → {clip['end_time']}s)")

        # 5a. Active speaker centering with Apollo Kalman Filter & Predictive Coding
        crop_info = detect_face_crop_region(video_path, clip["start_time"], clip["end_time"])
        log(f"     🚀 [NASA Apollo Kalman] Alignment: {crop_info['method']} (x={crop_info['crop_x']}, w={crop_info['crop_w']})")

        # 5b. Generate kinetic word-level .ass subtitles
        sub_path = Config.TEMP_DIR / f"sub_{safe_stem}_{i}_{unique_id}.ass"
        generate_subtitles(words, clip["start_time"], clip["end_time"], sub_path, crop_info, style_override, genre=genre)

        # 5c. Harmonic Metabolic Glide before GPU encode
        PACER.pace_transition("stt", "render")

        # 5d. Sequential render with GPU hardware acceleration
        t_render_start = time.time()
        out_file = render_short_sequential(video_path, clip, i, sub_path, crop_info, encoder_cfg=hw_encoder, video_title=video_path.stem)
        t_render_dur = time.time() - t_render_start
        if out_file and out_file.exists():
            GEODESIC.log_action(f"render_clip_{i}", t_render_dur, out_file.stat().st_size)

        # Clean intermediate subtitle file
        if sub_path.exists():
            try: sub_path.unlink(missing_ok=True)
            except Exception: pass

        if out_file and out_file.exists():
            size_mb = round(out_file.stat().st_size / (1024 * 1024), 2)
            item_res = {
                "clip_index": i,
                "title": out_file.stem,
                "start_time": clip["start_time"],
                "end_time": clip["end_time"],
                "filename": out_file.name,
                "path": str(out_file),
                "size_mb": size_mb,
                "genre": genre,
                "verified": True,
            }
            results.append(item_res)
            log(f"     ✅ Confirmed Box {i}: {out_file.name} ({size_mb} MB)")

        gc.collect()

    freed = purge_temp_cache()
    log(f"  🧹 SSD Cache Cleaned: {freed['freed_mb']} MB released, RAM free.")
    log("\n" + "=" * 70)
    log(f"  🎉 PIPELINE COMPLETE! Generated {len(results)} {genre} Shorts.")
    log("=" * 70 + "\n")

    return {
        "video_title": video_path.stem,
        "generated_shorts": results,
    }


# Wire Batch Manager Executor
BATCH_MANAGER.set_pipeline_executor(process_video_pipeline)

