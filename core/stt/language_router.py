"""
Language Router & Prompt Anchoring for Speech-to-Text.
Determines whether to translate or transcribe natively, and anchors Whisper
so that native speech (e.g. Hindi, Punjabi, Urdu) is not hallucinated or translated
when the user chooses 'original' mode.
"""

from typing import Tuple, Optional


def configure_stt_language_routing(
    locked_lang: Optional[str],
    lang_confidence: float,
    sub_language_mode: str,
    log_callback=None
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Returns (task, target_lang, initial_prompt).

    Modes:
    1. 'original' (default): Transcribes native lyrics/vocals phonetically into clean Romanized Latin characters (sing-along, zero machine translation).
    2. 'en_translate': Translates foreign speech/lyrics into English semantic meaning.
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            try: log_callback(msg)
            except Exception: pass

    is_translate = (sub_language_mode in ("en_translate", "translate"))

    if is_translate:
        task = "translate"
        target_lang = None  # Whisper translates into English
        prompt = "Translate clearly into natural English subtitles."
        log(f"  🌐 [STT Language Router] Mode: Translation into English (Detected: {str(locked_lang).upper()}, conf={lang_confidence:.2f})")
    else:
        task = "transcribe"
        target_lang = locked_lang
        # In original sing-along mode, if Hindi/Punjabi/Urdu is spoken, anchor decoder to native script
        # so Whisper NEVER translates into English semantic words!
        if locked_lang in ("hi", "pa", "ur"):
            prompt = "Yeh Hindi bol rahe hain. Jo bola wohi likhein bina translate kiye."
        else:
            prompt = None
        log(f"  🗣️ [STT Language Router] Mode: Original Spoken (Locked to {str(locked_lang).upper()}, conf={lang_confidence:.2f} -> Romanized English Letters)")

    return task, target_lang, prompt

