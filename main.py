"""
=============================================================================
  AUTOCLIP STUDIO — HIGH-PERFORMANCE ZERO-RAM & GENRE KINETIC PIPELINE
=============================================================================
  Enterprise Modular Architecture (Google Gemini Ultra Pro Inspired)
  - core/biomimetic: P-Core pinning, Laminar memory governor, 10-Route mesh
  - core/ingestion: YouTube downloader and local media inspector
  - core/audio: Zero-delay 80-8000Hz bandpass vocal extraction & transliteration
  - core/stt: Warmed faster-whisper singleton with Hindi prompt anchoring
  - core/clipping: Genre-based Ollama prompts & algorithmic speech density scanner
  - core/tracking: Active speaker face tracking with Apollo 1D Kalman filter
  - core/subtitles: Kinetic syllable pop, radiant glow, and dual typography
  - core/rendering: Sequential GPU hardware-accelerated transcoding (NVENC/QSV)
  - core/queue: Multi-user concurrent batch manager with session isolation
=============================================================================
"""

import sys
import os

# Thread affinity and Windows UTF-8 encoding
os.environ.setdefault("OMP_NUM_THREADS", "6")
os.environ.setdefault("MKL_NUM_THREADS", "6")
os.environ["KMP_AFFINITY"] = "none"

if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Re-export core interface for complete backward compatibility
from core.config import (
    Config,
    GOOGLE_FONTS_CATALOG,
    GENRE_THEMES,
    SUBTITLE_PRESETS,
    ensure_directories,
    purge_temp_cache,
    get_system_memory_info,
)
from core.biomimetic import (
    TOPOLOGY,
    LaminarMemoryGovernor,
    starling_affinity_lock,
    HarmonicPipelinePacer,
    LeastActionGeodesic,
    ROUTE_MESH,
)
from core.biomimetic.pacing import PACER, GEODESIC
from core.ingestion import (
    download_video,
    inspect_youtube_video,
    inspect_local_video,
)
from core.audio import (
    extract_and_chunk_audio,
    romanize_to_latin,
)
from core.stt import (
    get_warmed_whisper_pipeline,
    purge_whisper_cache,
    transcribe_audio_streamed,
)
from core.clipping import (
    GENRE_CRITERIA_MAP,
    check_ollama,
    algorithmic_genre_clips,
    create_full_video_boxes,
    find_best_clips_genre,
)
from core.tracking import (
    KalmanCropTracker,
    PredictiveFrameGator,
    ShannonEntropyGator,
    detect_face_crop_region,
    disk_frame_streamer,
)

from core.subtitles import (
    ensure_font,
    generate_subtitles,
    seconds_to_ass_time,
    hex_to_ass_color,
)
from core.rendering import (
    detect_hardware_encoder,
    check_ffmpeg,
    render_short_sequential,
)
from core.queue import (
    GenerationJob,
    BatchQueueManager,
    BATCH_MANAGER,
)
from core.pipeline import process_video_pipeline


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
