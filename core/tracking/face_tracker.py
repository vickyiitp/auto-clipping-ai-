"""
Active Speaker Face Tracking and Auto-Reframe Engine.
Detects active faces, calculates 9:16 vertical crop boxes,
applies Apollo 1D Kalman smoothing, and generates continuous FFmpeg crop pan expressions.
"""

import gc
from pathlib import Path
from typing import Generator, Tuple, Any
import cv2

from core.config import Config
from core.tracking.kalman_filter import KalmanCropTracker
from core.tracking.predictive_gator import PredictiveFrameGator, ShannonEntropyGator


def disk_frame_streamer(video_path: Path, start_time: float, end_time: float,
                        sample_count: int = 25) -> Generator[Tuple[float, Any], None, None]:
    """
    Python generator reading exactly ONE frame from SSD at a time.
    Guarantees zero-RAM accumulation.
    """
    cap = cv2.VideoCapture(str(video_path))
    try:
        duration = end_time - start_time
        interval = duration / max(1, sample_count)
        for i in range(sample_count):
            t_sec = start_time + (i * interval)
            cap.set(cv2.CAP_PROP_POS_MSEC, t_sec * 1000)
            ret, frame = cap.read()
            if ret and frame is not None:
                yield t_sec, frame
                del frame
    finally:
        cap.release()
        del cap
        gc.collect()


def detect_face_crop_region(video_path: Path, start_time: float, end_time: float) -> dict:
    """
    Dynamic Face Tracking & Auto-Reframe Engine.
    Samples frames across start, middle, and end of the clip timeline,
    detects active faces, smooths movement with Kalman filtering, detects shot cuts,
    and constructs a dynamic FFmpeg time-varying crop expression so persons on the
    left, right, or center are never cut off.
    """
    cascade_filename = "haarcascade_frontalface_default.xml"
    cascade_path = Config.BASE_DIR / cascade_filename
    if not cascade_path.exists():
        cascade_path = Path(cv2.data.haarcascades) / cascade_filename

    face_cascade = cv2.CascadeClassifier(str(cascade_path)) if cascade_path.exists() else None

    # Get video dimensions
    cap = cv2.VideoCapture(str(video_path))
    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)

    target_aspect = 9.0 / 16.0
    crop_h = fh
    crop_w = int(fh * target_aspect)
    if crop_w > fw:
        crop_w = fw
        crop_h = int(fw / target_aspect)

    max_x = max(0, fw - crop_w)
    center_x = max(0, (fw - crop_w) // 2)
    crop_y = max(0, (fh - crop_h) // 2)

    duration = max(1.0, end_time - start_time)
    num_samples = max(4, min(7, int(duration / 5.0) + 1))
    sample_interval = duration / max(1, num_samples - 1)

    raw_points = []
    frame_gator = PredictiveFrameGator(delta_threshold=0.04)
    shannon_gator = ShannonEntropyGator(entropy_threshold=0.08)
    last_detected_cx = None

    if face_cascade and not face_cascade.empty():
        for i in range(num_samples):
            rel_t = round(i * sample_interval, 2)
            abs_t = min(end_time, start_time + rel_t)
            cap.set(cv2.CAP_PROP_POS_MSEC, abs_t * 1000)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            h, w = frame.shape[:2]
            scale = 320.0 / max(h, w) if max(h, w) > 320 else 1.0
            small_frame = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1.0 else frame
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

            should_run_cascade = frame_gator.should_evaluate(gray) and shannon_gator.has_novelty(gray)
            if should_run_cascade:
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=3, minSize=(24, 24))
                if len(faces) > 0:
                    largest = max(faces, key=lambda f: f[2] * f[3])
                    fx, fy, fw_f, fh_f = largest
                    cx = int((fx + fw_f // 2) / scale) if scale < 1.0 else (fx + fw_f // 2)
                    last_detected_cx = cx
                    target_x = max(0, min(cx - crop_w // 2, max_x))
                    raw_points.append({"t": rel_t, "x": target_x, "detected": True})
                else:
                    raw_points.append({"t": rel_t, "x": None, "detected": False})
            else:
                if last_detected_cx is not None:
                    target_x = max(0, min(last_detected_cx - crop_w // 2, max_x))
                    raw_points.append({"t": rel_t, "x": target_x, "detected": True})
                else:
                    raw_points.append({"t": rel_t, "x": None, "detected": False})
            del gray
            del frame

    cap.release()
    del cap

    valid_points = [p for p in raw_points if p["x"] is not None]
    if not valid_points:
        return {
            "crop_x": center_x,
            "crop_y": crop_y,
            "crop_w": crop_w,
            "crop_h": crop_h,
            "crop_expr": f"{center_x}",
            "method": "center_crop",
        }

    first_detected = valid_points[0]["x"]
    last_x = first_detected
    for p in raw_points:
        if p["x"] is None:
            p["x"] = last_x
        else:
            last_x = p["x"]

    kalman = KalmanCropTracker(process_noise=2.0, measurement_noise=10.0, cut_threshold=280.0)
    smoothed = []
    for p in raw_points:
        filtered_val = kalman.update(p["x"])
        smoothed.append(int(filtered_val) if filtered_val is not None else center_x)

    key_points = []
    for i, p in enumerate(raw_points):
        x_val = smoothed[i]
        if not key_points:
            key_points.append({"t": p["t"], "x": x_val})
        else:
            if abs(x_val - key_points[-1]["x"]) >= 30 or i == len(raw_points) - 1:
                key_points.append({"t": p["t"], "x": x_val})

    if len(key_points) <= 1 or max(p["x"] for p in key_points) - min(p["x"] for p in key_points) < 40:
        final_x = key_points[0]["x"] if key_points else center_x
        return {
            "crop_x": final_x,
            "crop_y": crop_y,
            "crop_w": crop_w,
            "crop_h": crop_h,
            "crop_expr": f"{final_x}",
            "method": "static_face_centered",
        }

    def make_expr(idx):
        if idx >= len(key_points) - 1:
            return f"{key_points[-1]['x']}"
        p0 = key_points[idx]
        p1 = key_points[idx + 1]
        t0, x0 = p0["t"], p0["x"]
        t1, x1 = p1["t"], p1["x"]
        dt = max(0.1, t1 - t0)

        if abs(x1 - x0) <= 20:
            seg_expr = f"{x0}"
        else:
            seg_expr = f"({x0} + ({x1 - x0}) * (t - {t0:.2f}) / {dt:.2f})"

        next_part = make_expr(idx + 1)
        return f"if(lt(t\\,{t1:.2f})\\,{seg_expr}\\,{next_part})"

    full_expr = f"min(max(0\\,{make_expr(0)})\\,{max_x})"

    return {
        "crop_x": int(key_points[0]["x"]),
        "crop_y": crop_y,
        "crop_w": crop_w,
        "crop_h": crop_h,
        "crop_expr": full_expr,
        "method": f"dynamic_face_tracking ({len(key_points)} keyframes)",
    }

