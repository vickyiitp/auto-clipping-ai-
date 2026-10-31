"""
High-Throughput Streamed Audio Transcriber.
Implements SSD chunked transcription, anti-hallucination, song VAD bypass,
and millisecond-precision word duration clamping.
"""

import time
from pathlib import Path
from typing import List, Tuple

from core.stt.whisper_engine import get_warmed_whisper_pipeline
from core.stt.language_router import configure_stt_language_routing
from core.audio.transliteration import romanize_to_latin
from core.biomimetic.topology import starling_affinity_lock
from core.biomimetic.memory_governor import LaminarMemoryGovernor
from core.biomimetic.pacing import GEODESIC
from core.biomimetic.route_mesh import ROUTE_MESH


def transcribe_audio_streamed(
    chunk_files: List[Path],
    chunk_sec: float = 300.0,
    sub_language_mode: str = "original",
    genre: str = "Podcast",
    log_callback=None
) -> Tuple[List[dict], str]:
    """
    High-throughput chunked audio transcription using warmed Faster-Whisper singleton.
    Supports TWO distinct non-overlapping modes:
    1. 'original' (default): Transcribes native lyrics/vocals phonetically into clean Romanized Latin characters (sing-along, zero machine translation).
    2. 'en_translate': Translates foreign speech/lyrics into English semantic meaning.
    Anti-hallucination enabled: condition_on_previous_text=False + Silero VAD + no_speech_prob filtering skips instrumental pauses.
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            try: log_callback(msg)
            except Exception: pass

    is_translate = (sub_language_mode in ("en_translate", "translate"))
    mode_label = "ENGLISH TRANSLATION" if is_translate else "ORIGINAL SPOKEN (SING-ALONG IN ENGLISH LETTERS)"

    log("\n" + "=" * 70)
    log(f"  🗣️  STEP 3: HIGH-THROUGHPUT WHISPER STT (Mode: {mode_label} • Genre: {genre.upper()})")
    log("=" * 70)

    # Acquire warmed Faster-Whisper singleton (0s latency on subsequent calls)
    pipeline, model = get_warmed_whisper_pipeline(log_callback=log)

    is_song = (genre.lower() in ("song", "music", "music video"))
    use_vad = not is_song  # Bypass Silero VAD on songs to prevent dropping singing lyrics
    vad_params = dict(min_silence_duration_ms=400, speech_pad_ms=300, threshold=0.35) if use_vad else None

    # Step 3a: Universal Vocal Sensor — Detect Language ONCE on first chunk
    locked_lang = None
    lang_confidence = 0.0
    first_chunk = chunk_files[0] if chunk_files else None
    if first_chunk and first_chunk.exists():
        try:
            _, initial_info = model.transcribe(str(first_chunk), beam_size=1, max_initial_timestamp=20.0)
            locked_lang = initial_info.language
            lang_confidence = getattr(initial_info, "language_probability", 0.9)
        except Exception:
            locked_lang = "en"
            lang_confidence = 0.5

    task, target_lang, prompt = configure_stt_language_routing(
        locked_lang=locked_lang,
        lang_confidence=lang_confidence,
        sub_language_mode=sub_language_mode,
        log_callback=log
    )

    if is_song:
        log("  🎵 [Acoustic VAD Bypass] Music Video / Song detected: Silero VAD bypassed to preserve 100% of vocal melody.")

    all_words = []
    full_text_lines = []
    last_seg_text = ""

    LaminarMemoryGovernor.guard_memory_pressure(log_callback=log)

    for idx, chunk_file in enumerate(chunk_files):
        time_offset = idx * chunk_sec
        log(f"  🎙️ Transcribing chunk {idx+1}/{len(chunk_files)} ({chunk_file.name}) with P-Core Affinity Lock...")

        t_stt_chunk_start = time.time()

        def _tier1_standard_model():
            with starling_affinity_lock("p_cores"):
                segs, _ = model.transcribe(
                    str(chunk_file),
                    language=target_lang,
                    task=task,
                    beam_size=1,
                    best_of=1,
                    word_timestamps=True,
                    condition_on_previous_text=False,
                    vad_filter=use_vad,
                    vad_parameters=vad_params,
                    no_speech_threshold=0.6,
                    initial_prompt=prompt,
                )
                return list(segs)

        def _tier2_batched_pipeline():
            if pipeline is None:
                raise RuntimeError("Batched pipeline not initialized")
            with starling_affinity_lock("p_cores"):
                segs, _ = pipeline.transcribe(
                    str(chunk_file),
                    language=target_lang,
                    task=task,
                    batch_size=8,
                    beam_size=1,
                    word_timestamps=True,
                    condition_on_previous_text=False,
                    vad_filter=use_vad,
                    vad_parameters=vad_params,
                    initial_prompt=prompt,
                )
                return list(segs)

        def _tier3_unfiltered_fallback():
            segs, _ = model.transcribe(
                str(chunk_file),
                task=task,
                beam_size=1,
                word_timestamps=True,
                vad_filter=False,
            )
            return list(segs)

        chunk_segments = ROUTE_MESH.execute("R3_STT_TRANSCRIBE", [
            ("Tier 1: P-Core Faster-Whisper Model", _tier1_standard_model),
            ("Tier 2: Batched Inference Pipeline", _tier2_batched_pipeline),
            ("Tier 3: Unfiltered Robust Passthrough", _tier3_unfiltered_fallback),
        ], log_callback=log)

        for segment in (chunk_segments or []):
            # For non-song speech, filter out low-confidence pause noise; in songs, preserve all singing lyrics
            if not is_song and getattr(segment, "no_speech_prob", 0) > 0.70:
                continue

            seg_text = segment.text.strip()
            if not is_translate and seg_text:
                seg_text = romanize_to_latin(seg_text)

            # Prevent repetitive loop hallucinations
            if seg_text and seg_text.lower() == last_seg_text.lower():
                continue

            if seg_text:
                last_seg_text = seg_text
                full_text_lines.append(seg_text)

            if segment.words:
                for w in segment.words:
                    word_clean = w.word.strip()
                    if not is_translate and word_clean:
                        word_clean = romanize_to_latin(word_clean)
                    if word_clean:
                        w_start = round(w.start + time_offset, 3)
                        w_end = round(w.end + time_offset, 3)
                        # Anti-drift: clamp word duration to maximum 2.0s so subtitles never linger during pauses
                        if w_end - w_start > 2.0:
                            w_end = round(w_start + min(1.2, 0.25 * max(2, len(word_clean))), 3)
                        all_words.append({
                            "word": word_clean,
                            "start": w_start,
                            "end": w_end,
                            "probability": round(getattr(w, "probability", 0.9), 2),
                        })
            elif seg_text:
                # Fallback: if word_timestamps is empty, split segment into words
                words_in_seg = seg_text.split()
                if words_in_seg:
                    dur = max(0.18, (segment.end - segment.start) / len(words_in_seg))
                    for i_w, w_str in enumerate(words_in_seg):
                        w_clean = w_str.strip()
                        if not is_translate and w_clean:
                            w_clean = romanize_to_latin(w_clean)
                        if w_clean:
                            w_st = round(segment.start + time_offset + i_w * dur, 3)
                            w_et = round(min(segment.end, segment.start + (i_w + 1) * dur) + time_offset, 3)
                            if w_et - w_st > 2.0:
                                w_et = round(w_st + min(1.2, 0.25 * max(2, len(w_clean))), 3)
                            all_words.append({
                                "word": w_clean,
                                "start": w_st,
                                "end": w_et,
                                "probability": 0.85,
                            })

        # Remove temporary chunk from SSD as soon as consumed (unless it's full audio)
        chunk_sz = chunk_file.stat().st_size if chunk_file.exists() else (1024 * 1024)
        if chunk_file.name.startswith("chunk_"):
            try: chunk_file.unlink(missing_ok=True)
            except Exception: pass

        t_stt_dur = time.time() - t_stt_chunk_start
        GEODESIC.log_action(f"stt_chunk_{idx+1}", t_stt_dur, chunk_sz)

    full_transcript = " ".join(full_text_lines)
    log(f"  ✅ STT Complete: {len(all_words)} words parsed with millisecond precision.")

    return all_words, full_transcript

