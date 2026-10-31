"""
AutoClip Core Package - High-Performance Enterprise Multi-User Architecture.
"""

from core.config import Config, GOOGLE_FONTS_CATALOG, GENRE_THEMES, SUBTITLE_PRESETS
from core.pipeline import process_video_pipeline
from core.queue.batch_manager import BATCH_MANAGER, BatchQueueManager
from core.queue.job_models import GenerationJob

__all__ = [
    "Config",
    "GOOGLE_FONTS_CATALOG",
    "GENRE_THEMES",
    "SUBTITLE_PRESETS",
    "process_video_pipeline",
    "BATCH_MANAGER",
    "BatchQueueManager",
    "GenerationJob",
]

