"""
Media Ingestion Module: Downloads YouTube videos and loads local files.
"""

from core.ingestion.downloader import download_video, inspect_youtube_video
from core.ingestion.local_loader import inspect_local_video

__all__ = ["download_video", "inspect_youtube_video", "inspect_local_video"]

