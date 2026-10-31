"""
Local video loader and metadata inspector for AutoClip Studio.
Extracts duration, resolution, dimensions and generates lightweight preview thumbnails.
"""

import math
import gc
from pathlib import Path
import cv2
from core.config import Config


def inspect_local_video(file_path: Path) -> dict:
    """Pre-inspects local video metadata using OpenCV."""
    try:
        cap = cv2.VideoCapture(str(file_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        duration = int(frame_count / fps) if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)

        Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        thumb_name = f"thumb_{file_path.stem}.jpg"
        thumb_path = Config.TEMP_DIR / thumb_name

        cap.set(cv2.CAP_PROP_POS_MSEC, min(1000, duration * 500))
        ret, frame = cap.read()
        if ret and frame is not None:
            cv2.imwrite(str(thumb_path), frame)
            del frame
        cap.release()
        del cap
        gc.collect()

        mins = duration // 60
        secs = duration % 60
        dur_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

        return {
            "title": file_path.stem.replace("_", " ").title(),
            "duration": duration,
            "duration_str": dur_str,
            "thumbnail": f"/api/thumb/{thumb_name}",
            "max_height": height,
            "quality_label": f"{width}x{height}",
            "has_ultra": height > 1080,
            "boxes_15s": max(1, math.ceil(duration / 15.0)) if duration else 1,
            "boxes_30s": max(1, math.ceil(duration / 30.0)) if duration else 1,
            "boxes_45s": max(1, math.ceil(duration / 45.0)) if duration else 1,
            "boxes_60s": max(1, math.ceil(duration / 60.0)) if duration else 1,
            "local_path": str(file_path),
        }
    except Exception as e:
        print(f"  ⚠️ Local inspect error: {e}")
        return {
            "title": file_path.name,
            "duration": 0,
            "duration_str": "Unknown",
            "thumbnail": "",
            "max_height": 0,
            "quality_label": "Unknown",
            "has_ultra": False,
            "boxes_15s": 1,
            "boxes_30s": 1,
            "boxes_45s": 1,
            "boxes_60s": 1,
            "local_path": str(file_path),
        }

