"""
Audio and subtitle transliteration module.
Converts native non-Latin alphabets (Devanagari, Gurmukhi, Arabic, Hangul, Kanji, etc.)
into clean, readable phonetic English (Latin) alphabet so viewers can sing along.
"""

import re


def romanize_to_latin(text: str) -> str:
    """
    Converts native non-Latin scripts (Devanagari, Gurmukhi, Arabic, Hangul, Kanji, etc.)
    into clean, readable phonetic English (Latin) alphabet so viewers can sing along.
    Removes odd artifacts like orphan apostrophes while preserving vocal rhythm.
    """
    if not text:
        return ""
    try:
        import anyascii
        latin = anyascii.anyascii(text)
        latin = re.sub(r"'(?=[a-zA-Z])", "", latin)
        return re.sub(r"\s+", " ", latin).strip()
    except Exception:
        cleaned = re.sub(r'[^\x00-\x7F]+', ' ', text)
        return re.sub(r"\s+", " ", cleaned).strip()

