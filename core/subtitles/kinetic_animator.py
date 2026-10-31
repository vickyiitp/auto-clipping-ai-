"""
Kinetic Typography & ASS Subtitle Generation Module.
Generates word-level ASS subtitles featuring:
- Kinetic Word Pop (120% scale on syllable hit)
- Radiant Neon Glow
- Clean syllable timing
- Dual Typography (Header Sans + Golden Calligraphy Accent)
"""

from pathlib import Path
from typing import List

from core.config import Config, GENRE_THEMES
from core.subtitles.font_manager import ensure_font


def seconds_to_ass_time(seconds: float) -> str:
    """Converts seconds into ASS timestamp format H:MM:SS.cc"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


def hex_to_ass_color(color_str: str) -> str:
    """
    Converts web hex colors (#RRGGBB or #RGB) into ASS color format &H00BBGGRR&.
    If already in ASS format (&H...), preserves it cleanly.
    """
    if not color_str:
        return "&H00FFFFFF&"
    color_str = str(color_str).strip()
    if color_str.startswith("&H") or color_str.startswith("&h"):
        if not color_str.endswith("&"):
            return color_str + "&"
        return color_str

    c = color_str.lstrip("#")
    if len(c) == 3:
        c = "".join([x * 2 for x in c])
    if len(c) >= 6:
        r = c[0:2]
        g = c[2:4]
        b = c[4:6]
        return f"&H00{b.upper()}{g.upper()}{r.upper()}&"
    return "&H00FFFFFF&"


def generate_subtitles(words: List[dict], start_time: float, end_time: float,
                       output_path: Path, crop_info: dict,
                       style_override: dict = None,
                       genre: str = "Podcast") -> Path:
    """
    Programmatically creates .ASS subtitle files featuring:
    - Kinetic Word Pop: Active words bounce out to 120% scale on syllable hit (TikTok/Reels karaoke style)
    - Radiant Neon Glow: Vibrant colored edge aura tuned to musical genre
    - Clean timing: Subtitles display ONLY when real words are spoken/sung; zero clutter or fake badges on pauses
    - Dual typography support: Bold Header + Golden handwritten cursive accent
    - User Customizable Text Colors: Active word highlight, resting text, outline, and glowing aura.
    """
    theme = dict(GENRE_THEMES.get(genre, GENRE_THEMES["Podcast"]))
    if style_override:
        theme.update({k: v for k, v in style_override.items() if v is not None})

    font_key        = theme.get("font_name", "Montserrat-Black")
    font_family     = ensure_font(font_key)
    font_size       = int(theme.get("custom_sub_size") or theme.get("font_size") or (68 if genre.lower() == "song" else 58))

    # Color customization resolution with hex-to-ASS converter
    raw_highlight   = theme.get("custom_highlight_color") or theme.get("highlight_color", "&H00FFFF00&")
    raw_primary     = theme.get("custom_primary_color") or theme.get("primary_color", "&H00FFFFFF&")
    raw_outline     = theme.get("custom_outline_color") or theme.get("outline_color", "&H00000000&")
    raw_glow        = theme.get("custom_glow_color") or theme.get("glow_color", "&H00FF00FF&" if genre.lower() == "song" else raw_outline)

    highlight_color = hex_to_ass_color(raw_highlight)
    primary_color   = hex_to_ass_color(raw_primary)
    outline_color   = hex_to_ass_color(raw_outline)
    glow_color      = hex_to_ass_color(raw_glow)

    outline_width   = int(theme.get("custom_outline_width") if theme.get("custom_outline_width") is not None else theme.get("outline_width", 6))
    shadow          = int(theme.get("custom_shadow") if theme.get("custom_shadow") is not None else theme.get("shadow", 4))
    uppercase       = bool(theme.get("uppercase", True) if theme.get("custom_uppercase") is None else theme.get("custom_uppercase"))
    words_per_line  = max(1, min(6, int(theme.get("words_per_line", 2))))
    highlight_active= theme.get("highlight_words", True)
    sub_pos         = str(theme.get("sub_position", "bottom")).lower()

    # Advanced Video Editor Controls
    dual_mode            = bool(theme.get("dual_mode", False))
    secondary_font_key   = theme.get("secondary_font", "GreatVibes-Regular")
    secondary_font_family= ensure_font(secondary_font_key)
    glow_style           = theme.get("glow_style")

    if glow_style == "rose" and not theme.get("custom_glow_color"):
        glow_color = "&H006633FF&"
        highlight_color = "&H00E8F0FF&"
    elif glow_style == "gold" and not theme.get("custom_glow_color"):
        glow_color = "&H000088FF&"
        highlight_color = "&H0018C5F5&"
    elif glow_style == "magenta" and not theme.get("custom_glow_color"):
        glow_color = "&H008000FF&"
        highlight_color = "&H00D600FF&"
    elif glow_style == "cyan" and not theme.get("custom_glow_color"):
        glow_color = "&H00FFFF00&"
        highlight_color = "&H0000FFFF&"
    elif glow_style == "shadow" and not theme.get("custom_glow_color"):
        glow_color = "&H00000000&"

    if "top" in sub_pos:
        alignment = 8
        margin_v = 220
    elif "center" in sub_pos or "middle" in sub_pos or "centre" in sub_pos:
        alignment = 5
        margin_v = 0
    else:  # bottom
        alignment = 2
        margin_v = 360

    clip_duration = max(1.0, end_time - start_time)
    clip_words = [w for w in words if w["end"] >= start_time - 0.1 and w["start"] <= end_time + 0.1]

    if not clip_words:
        output_path.write_text("", encoding="utf-8")
        return output_path

    spoken_events = []
    for i in range(0, len(clip_words), words_per_line):
        group = clip_words[i:i + words_per_line]
        raw_start = group[0]["start"] - start_time
        raw_end = group[-1]["end"] - start_time

        group_start = max(0.0, raw_start)
        group_end = min(clip_duration, max(group_start + 0.22, raw_end + 0.08))

        if dual_mode:
            accent_size = int(font_size * 1.25)
            if len(group) >= 2:
                header_words = [w["word"].strip().upper() if uppercase else w["word"].strip() for w in group[:-1]]
                header_txt = " ".join(header_words)
                accent_word = group[-1]["word"].strip()
                accent_txt = accent_word.title() if not uppercase else accent_word
                colored_text = f"{{\\fn{font_family}\\fs{font_size}\\c{primary_color}\\b1}}{header_txt}\\N{{\\fn{secondary_font_family}\\fs{accent_size}\\c{highlight_color}\\blur4\\3c{glow_color}}}{accent_txt}"
            else:
                w_txt = group[0]["word"].strip()
                header_txt = w_txt.upper() if uppercase else w_txt
                accent_txt = w_txt.title()
                colored_text = f"{{\\fn{font_family}\\fs{font_size}\\c{primary_color}\\b1}}{header_txt}\\N{{\\fn{secondary_font_family}\\fs{accent_size}\\c{highlight_color}\\blur4\\3c{glow_color}}}{accent_txt}"

            spoken_events.append({
                "start": group_start,
                "end": group_end,
                "text": colored_text,
            })
        elif len(group) == 1 or not highlight_active:
            tokens = []
            for w in group:
                wt = w["word"].strip()
                if uppercase: wt = wt.upper()
                tokens.append(wt)
            joined_txt = " ".join(tokens)
            if highlight_active:
                colored_text = f"{{\\blur6\\3c{glow_color}\\c{highlight_color}\\t(0,90,\\fscx124\\fscy124\\frz-2)\\t(90,190,\\fscx100\\fscy100\\frz0)}}{joined_txt}"
            else:
                colored_text = f"{{\\c{primary_color}}}{joined_txt}"
            spoken_events.append({
                "start": group_start,
                "end": group_end,
                "text": colored_text,
            })
        else:
            n_words = len(group)
            for k in range(n_words):
                wk_raw_start = group[k]["start"] - start_time
                wk_start = max(group_start, wk_raw_start)
                if k < n_words - 1:
                    wk_next_start = group[k + 1]["start"] - start_time
                    wk_end = max(wk_start + 0.08, min(wk_next_start, group_end))
                else:
                    wk_end = group_end

                if wk_end <= wk_start:
                    wk_end = wk_start + 0.15

                tokens = []
                for idx_w, w_item in enumerate(group):
                    w_txt = w_item["word"].strip()
                    if uppercase:
                        w_txt = w_txt.upper()
                    if idx_w == k and highlight_active:
                        tilt_angle = -2 if (k % 2 == 0) else 2
                        tokens.append(f"{{\\blur6\\3c{glow_color}\\c{highlight_color}\\t(0,90,\\fscx124\\fscy124\\frz{tilt_angle})\\t(90,190,\\fscx100\\fscy100\\frz0)}}{w_txt}")
                    else:
                        tokens.append(f"{{\\rKinetic\\c{primary_color}}}{w_txt}")

                spoken_events.append({
                    "start": wk_start,
                    "end": wk_end,
                    "text": " ".join(tokens),
                })

    subtitle_events = spoken_events

    ass_header = f"""[Script Info]
Title: AutoClip Kinetic Subtitles
ScriptType: v4.00+
PlayResX: {Config.TARGET_WIDTH}
PlayResY: {Config.TARGET_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kinetic,{font_family},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},30,30,{margin_v},1
Style: KineticGlow,{font_family},{font_size},{highlight_color},&H000000FF,{glow_color},&H80000000,-1,0,0,0,100,100,1,0,1,{outline_width + 1},{shadow},{alignment},30,30,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogue_lines = []
    for ev in subtitle_events:
        st_str = seconds_to_ass_time(ev["start"])
        et_str = seconds_to_ass_time(ev["end"])
        dialogue_lines.append(f"Dialogue: 0,{st_str},{et_str},Kinetic,,0,0,0,,{ev['text']}")

    ass_content = ass_header + "\n".join(dialogue_lines) + "\n"
    output_path.write_text(ass_content, encoding="utf-8")
    return output_path

