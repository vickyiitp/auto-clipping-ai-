"""
Full Video Boxer Module.
Divides full duration into contiguous sequential boxes (e.g. 15s, 30s, 45s, 60s).
"""

import math
from typing import List


def create_full_video_boxes(total_duration: float, words: List[dict] = None, chunk_size_sec: float = 30.0) -> List[dict]:
    """Divides full duration into contiguous sequential boxes."""
    chunk_sec = max(10.0, float(chunk_size_sec or 30.0))
    num_boxes = max(1, math.ceil(total_duration / chunk_sec))
    boxes = []

    for idx in range(num_boxes):
        start = round(idx * chunk_sec, 2)
        end = round(min(total_duration, (idx + 1) * chunk_sec), 2)
        if end - start < 7.0 and boxes:
            boxes[-1]["end_time"] = end
            continue
        words_in_box = [w for w in (words or []) if w["end"] >= start - 0.3 and w["start"] <= end + 0.3]
        boxes.append({
            "title": f"Part {idx+1}",
            "start_time": start,
            "end_time": end,
            "reason": f"Box {idx+1}/{num_boxes} ({len(words_in_box)} spoken words)",
            "words_count": len(words_in_box),
        })
    return boxes

