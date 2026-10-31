"""
Hardware Acceleration Detector and FFmpeg Validator.
Tests NVIDIA NVENC, Intel Quick Sync (QSV), AMD AMF, and falls back to CPU libx264.
"""

import sys
import shutil
import subprocess

_CACHED_HW_ENCODER = None


def check_ffmpeg():
    """Validates FFmpeg is present in system PATH."""
    if not shutil.which("ffmpeg"):
        print("  ❌ FFmpeg is NOT installed or not in PATH!")
        sys.exit(1)


def detect_hardware_encoder() -> dict:
    """
    Auto-detects available GPU hardware acceleration for FFmpeg.
    Tests Intel QSV (h264_qsv), NVIDIA NVENC (h264_nvenc), AMD AMF (h264_amf),
    or gracefully falls back to CPU libx264.
    """
    global _CACHED_HW_ENCODER
    if _CACHED_HW_ENCODER is not None:
        return _CACHED_HW_ENCODER

    test_encoders = [
        {
            "name": "h264_nvenc",
            "type": "NVIDIA NVENC (GPU)",
            "args": ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23"],
        },
        {
            "name": "h264_qsv",
            "type": "Intel Quick Sync (GPU/iGPU)",
            "args": ["-c:v", "h264_qsv", "-preset", "veryfast", "-global_quality", "23", "-look_ahead", "0"],
        },
        {
            "name": "h264_amf",
            "type": "AMD AMF (GPU)",
            "args": ["-c:v", "h264_amf", "-quality", "balanced"],
        },
        {
            "name": "libx264",
            "type": "CPU (Optimized libx264)",
            "args": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"],
        },
    ]

    for enc in test_encoders:
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.2",
            *enc["args"], "-f", "null", "-"
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
            if res.returncode == 0:
                _CACHED_HW_ENCODER = enc
                print(f"  ⚡ Hardware Encoder Detected: {enc['type']} [{enc['name']}]")
                return enc
        except Exception:
            continue

    _CACHED_HW_ENCODER = test_encoders[-1]
    return _CACHED_HW_ENCODER

