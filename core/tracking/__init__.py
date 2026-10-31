"""
Face Tracking and Auto-Reframe Module.
"""

from core.tracking.kalman_filter import KalmanCropTracker
from core.tracking.predictive_gator import PredictiveFrameGator, ShannonEntropyGator
from core.tracking.face_tracker import detect_face_crop_region, disk_frame_streamer

__all__ = [
    "KalmanCropTracker",
    "PredictiveFrameGator",
    "ShannonEntropyGator",
    "detect_face_crop_region",
    "disk_frame_streamer",
]

