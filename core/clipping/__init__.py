"""
Clip Detection and Boxing Module: Ollama LLM, algorithmic scanner, and full-video boxer.
"""

from core.clipping.genre_prompts import GENRE_CRITERIA_MAP, check_ollama
from core.clipping.algorithmic_scanner import algorithmic_genre_clips
from core.clipping.full_video_boxer import create_full_video_boxes
from core.clipping.clip_selector import find_best_clips_genre

__all__ = [
    "GENRE_CRITERIA_MAP",
    "check_ollama",
    "algorithmic_genre_clips",
    "create_full_video_boxes",
    "find_best_clips_genre",
]

