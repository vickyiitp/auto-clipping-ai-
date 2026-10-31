"""
Font Management Module.
Ensures TrueType (.ttf) font assets exist on SSD, auto-downloading from Google Fonts when needed.
"""

import urllib.request
from pathlib import Path
from core.config import Config, GOOGLE_FONTS_CATALOG


def ensure_font(font_key: str) -> str:
    """
    Ensures the specified font file (.ttf) exists on SSD in fonts/ directory.
    If not found, downloads it directly from Google Fonts repository.
    Returns the font family name to be passed into ASS subtitles.
    """
    Config.FONTS_DIR.mkdir(parents=True, exist_ok=True)

    font_info = GOOGLE_FONTS_CATALOG.get(font_key)
    if not font_info:
        return font_key

    font_family = font_info["family"]
    ttf_url = font_info["url"]
    if not ttf_url:
        return font_family

    dest_file = Config.FONTS_DIR / f"{font_key}.ttf"
    if not dest_file.exists() or dest_file.stat().st_size < 1024:
        print(f"  ⬇️  Downloading Google Font '{font_key}' to SSD...")
        try:
            req = urllib.request.Request(ttf_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp, open(dest_file, "wb") as out_f:
                out_f.write(resp.read())
            print(f"  ✅ Cached font to {dest_file.name}")
        except Exception as e:
            print(f"  ⚠️ Could not download font {font_key}: {e} (using fallback font)")
            return "Impact"

    return font_family

