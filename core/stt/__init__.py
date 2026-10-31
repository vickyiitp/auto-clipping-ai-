"""
Speech-to-Text Module: Whisper singleton, language routing, and streamed transcription.
"""

from core.stt.whisper_engine import get_warmed_whisper_pipeline, purge_whisper_cache
from core.stt.language_router import configure_stt_language_routing
from core.stt.transcriber import transcribe_audio_streamed

__all__ = [
    "get_warmed_whisper_pipeline",
    "purge_whisper_cache",
    "configure_stt_language_routing",
    "transcribe_audio_streamed",
]

