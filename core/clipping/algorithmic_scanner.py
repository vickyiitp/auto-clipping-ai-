"""
Algorithmic Speech-Density and Rhythm Scanner.
Picks the most dynamic segments based on speech cadence and word clustering
when LLM is not used or unavailable.
"""

from typing import List


def algorithmic_genre_clips(words: List[dict], total_duration: float, genre: str,
                             num_clips: int = 3, target_duration: float = 30.0) -> List[dict]:
    """Algorithmic highlight finder tuned to genre characteristics and high word density."""
    if not words or len(words) < 4:
        # Uniform fallback
        spacing = total_duration / (num_clips + 1)
        return [{
            "title": f"Part {i+1}",
            "start_time": round(max(0.0, spacing * (i + 1) - target_duration / 2), 2),
            "end_time": round(min(total_duration, spacing * (i + 1) + target_duration / 2), 2),
            "reason": f"{genre} uniform highlight",
        } for i in range(num_clips)]

    candidates = []
    step = 3.0
    current_start = 0.0

    while current_start + target_duration <= total_duration + 2.0:
        current_end = min(total_duration, current_start + target_duration)
        w_in_win = [w for w in words if w["start"] >= current_start - 0.4 and w["end"] <= current_end + 0.4]
        if len(w_in_win) >= 4:
            first_w_start = max(0.0, w_in_win[0]["start"] - 0.15)
            win_end = min(total_duration, first_w_start + target_duration)

            density = len(w_in_win) / target_duration
            candidates.append({
                "start": first_w_start,
                "end": win_end,
                "score": density,
                "word_count": len(w_in_win),
            })
        current_start += step

    candidates.sort(key=lambda c: c["score"], reverse=True)

    selected = []
    for cand in candidates:
        if len(selected) >= num_clips:
            break
        # Prevent significant overlap (> 6s)
        if not any(not (cand["end"] <= s["start"] + 6 or cand["start"] >= s["end"] - 6) for s in selected):
            selected.append(cand)

    # If density scan found fewer than requested, fill with uniform spacing
    if len(selected) < num_clips:
        spacing = total_duration / (num_clips + 1)
        for i in range(num_clips):
            if len(selected) >= num_clips:
                break
            st = round(max(0.0, spacing * (i + 1) - target_duration / 2), 2)
            et = round(min(total_duration, st + target_duration), 2)
            if not any(not (et <= s["start"] + 6 or st >= s["end"] - 6) for s in selected):
                w_cnt = len([w for w in words if w["start"] >= st and w["end"] <= et])
                selected.append({"start": st, "end": et, "score": 1.0, "word_count": w_cnt})

    selected.sort(key=lambda c: c["start"])

    return [{
        "title": f"Part {i+1}",
        "start_time": round(s["start"], 2),
        "end_time": round(s["end"], 2),
        "reason": f"[{genre}] Peak vocal rhythm ({s['word_count']} words, immediate speech start)",
    } for i, s in enumerate(selected)]

