"""
Clip Selector Orchestrator.
Coordinates between Full-Video boxing, Ollama Llama-3 AI highlights,
and algorithmic speech-density scanning.
"""

import re
import json
from typing import List

from core.config import Config
from core.clipping.genre_prompts import (
    GENRE_CRITERIA_MAP,
    LLMClipResponse,
    check_ollama,
    OLLAMA_AVAILABLE,
)
from core.clipping.full_video_boxer import create_full_video_boxes
from core.clipping.algorithmic_scanner import algorithmic_genre_clips

if OLLAMA_AVAILABLE:
    from ollama import chat


def find_best_clips_genre(words: List[dict], full_transcript: str,
                          genre: str = "Podcast",
                          clipping_mode: str = "smart_highlights",
                          chunk_size_sec: float = 30.0,
                          num_clips: int = 3,
                          clip_min_sec: float = 30.0,
                          clip_max_sec: float = 60.0,
                          video_duration: float = None) -> List[dict]:
    """
    Selects highlight clips dynamically using Ollama Llama-3 based on the selected Genre,
    or falls back to an intelligent genre-tuned phonetic speech-density scanner.
    """
    print("\n" + "=" * 70)
    print(f"  🤖  STEP 4: GENRE-BASED CLIP SELECTION (Genre: {genre.upper()} • Mode: {clipping_mode.upper()})")
    print("=" * 70)

    total_duration = video_duration if (video_duration and video_duration > 0) else (words[-1]["end"] if words else 60.0)

    if clipping_mode == "full_video":
        return create_full_video_boxes(total_duration, words, chunk_size_sec)

    genre_criteria = GENRE_CRITERIA_MAP.get(genre, GENRE_CRITERIA_MAP["Podcast"])

    # Attempt Ollama structured LLM inference
    if check_ollama():
        print(f"  🦙 Prompting Ollama ({Config.OLLAMA_MODEL}) with {genre} criteria...")
        system_prompt = (
            f"You are a viral YouTube Shorts and TikTok video editor specializing in the '{genre}' genre. "
            f"Selection Criteria for '{genre}': {genre_criteria}\n"
            f"Extract exactly {num_clips} highlight segments from the transcript. "
            f"Each clip MUST be between {clip_min_sec}s and {clip_max_sec}s long. "
            f"Ensure start_time starts immediately on a strong hook word."
        )

        user_content = f"Total video duration: {total_duration:.1f}s.\nTranscript:\n{full_transcript[:4000]}"

        try:
            response = chat(
                model=Config.OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                format=LLMClipResponse.model_json_schema(),
            )
            parsed = json.loads(response["message"]["content"])
            raw_clips = parsed.get("clips", [])
            valid_clips = []
            for c in raw_clips:
                st = max(0.0, float(c["start_time"]))
                et = min(total_duration, float(c["end_time"]))
                if et - st >= 10.0:
                    valid_clips.append({
                        "title": re.sub(r'[^\w\s-]', '', c["title"]).strip().replace(" ", "_")[:35],
                        "start_time": round(st, 2),
                        "end_time": round(et, 2),
                        "reason": f"[{genre}] {c.get('reason', 'High engagement moment')}",
                        "hook_score": c.get("hook_score", 9),
                    })
            if valid_clips:
                print(f"  ✅ Ollama selected {len(valid_clips)} {genre} highlights!")
                return valid_clips[:num_clips]
        except Exception as e:
            print(f"  ⚠️ Ollama inference skipped ({e}). Falling back to algorithmic genre scanner.")

    # Algorithmic Genre Speech-Density & Rhythm Scanner
    return algorithmic_genre_clips(words, total_duration, genre, num_clips, clip_min_sec)

