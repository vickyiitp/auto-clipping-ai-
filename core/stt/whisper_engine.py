"""
Whisper Engine Module: Cached faster-whisper singleton with P-Core pinning.
"""

import threading
import av

# PyAV 14+ compatibility patch for faster-whisper
_orig_av_open = av.open
def _compat_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _orig_av_open(*args, **kwargs)
av.open = _compat_av_open

from faster_whisper import WhisperModel, BatchedInferencePipeline
from core.config import Config
from core.biomimetic.topology import starling_affinity_lock

_CACHED_WHISPER_MODEL = None
_CACHED_WHISPER_PIPELINE = None
_WHISPER_LOCK = threading.Lock()


def get_warmed_whisper_pipeline(log_callback=None):
    """
    Returns warmed Faster-Whisper singleton model and batched inference pipeline.
    Locks matrix calculations to high-performance P-cores.
    """
    global _CACHED_WHISPER_MODEL, _CACHED_WHISPER_PIPELINE

    def log(msg: str):
        print(msg)
        if log_callback:
            try: log_callback(msg)
            except Exception: pass

    with _WHISPER_LOCK:
        if _CACHED_WHISPER_MODEL is None:
            log(f"  ⚡ Warming Whisper STT ({Config.WHISPER_MODEL_SIZE} on {Config.WHISPER_DEVICE}/{Config.WHISPER_COMPUTE})...")
            with starling_affinity_lock("p_cores"):
                try:
                    _CACHED_WHISPER_MODEL = WhisperModel(
                        Config.WHISPER_MODEL_SIZE,
                        device=Config.WHISPER_DEVICE,
                        compute_type=Config.WHISPER_COMPUTE,
                        cpu_threads=6,
                        num_workers=1,
                    )
                    _CACHED_WHISPER_PIPELINE = BatchedInferencePipeline(model=_CACHED_WHISPER_MODEL)
                    log("  ✅ Faster-Whisper singleton model warmed and resident in cache.")
                except Exception as e:
                    log(f"  ⚠️ Whisper CUDA/int8 load fallback: {e}")
                    _CACHED_WHISPER_MODEL = WhisperModel(
                        Config.WHISPER_MODEL_SIZE,
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=4,
                    )
                    _CACHED_WHISPER_PIPELINE = None

    return _CACHED_WHISPER_PIPELINE, _CACHED_WHISPER_MODEL


def purge_whisper_cache():
    """Explicitly releases Whisper model singleton from memory."""
    global _CACHED_WHISPER_MODEL, _CACHED_WHISPER_PIPELINE
    with _WHISPER_LOCK:
        _CACHED_WHISPER_MODEL = None
        _CACHED_WHISPER_PIPELINE = None

