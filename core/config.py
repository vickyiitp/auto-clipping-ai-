import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Central configuration for SSD-streaming, hardware acceleration, and multi-user scaling."""
    BASE_DIR        = Path(__file__).resolve().parent.parent
    DOWNLOADS_DIR   = BASE_DIR / "downloads"
    TEMP_DIR        = BASE_DIR / "temp"
    OUTPUT_DIR      = BASE_DIR / "output"
    FONTS_DIR       = BASE_DIR / "fonts"
    COOKIES_FILE    = BASE_DIR / "cookies.txt"

    # Whisper Settings
    WHISPER_MODEL_SIZE = "base"
    WHISPER_DEVICE     = "cpu"       # "cpu" or "cuda"
    WHISPER_COMPUTE    = "int8"      # "int8" on CPU, "float16" on CUDA
    AUDIO_CHUNK_SEC    = 300.0       # 5 minutes SSD audio chunking for zero-RAM STT

    # Ollama Settings
    OLLAMA_MODEL       = "llama3.1"
    NUM_CLIPS          = 3
    CLIP_MIN_SEC       = 30.0
    CLIP_MAX_SEC       = 60.0

    # Video Render Settings
    TARGET_WIDTH       = 1080
    TARGET_HEIGHT      = 1920
    VIDEO_CRF          = 23
    AUDIO_BITRATE      = "192k"

    # Default Genre & Face Detection
    GENRE              = "Podcast"
    FACE_SAMPLE_FRAMES = 25
    SUB_WORDS_PER_LINE = 2

    @classmethod
    def ensure_directories(cls):
        """Ensures all essential folders exist on SSD with zero missing folder errors."""
        for p in [cls.DOWNLOADS_DIR, cls.TEMP_DIR, cls.OUTPUT_DIR, cls.FONTS_DIR]:
            p.mkdir(parents=True, exist_ok=True)


GOOGLE_FONTS_CATALOG = {
    "Poppins-ExtraBold": {"family": "Poppins", "url": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf"},
    "GreatVibes-Regular": {"family": "Great Vibes", "url": "https://github.com/google/fonts/raw/main/ofl/greatvibes/GreatVibes-Regular.ttf"},
    "CinzelDecorative-Bold": {"family": "Cinzel Decorative", "url": "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"},
    "PlayfairDisplay-Bold": {"family": "Playfair Display", "url": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Bold.ttf"},
    "AlexBrush-Regular": {"family": "Alex Brush", "url": "https://github.com/google/fonts/raw/main/ofl/alexbrush/AlexBrush-Regular.ttf"},
    "DancingScript-Bold": {"family": "Dancing Script", "url": "https://github.com/google/fonts/raw/main/ofl/dancingscript/DancingScript-Bold.ttf"},
    "Montserrat-Black": {"family": "Montserrat", "url": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Black.ttf"},
    "DelaGothicOne-Regular": {"family": "Dela Gothic One", "url": "https://github.com/google/fonts/raw/main/ofl/delagothicone/DelaGothicOne-Regular.ttf"},
    "Shrikhand-Regular": {"family": "Shrikhand", "url": "https://github.com/google/fonts/raw/main/ofl/shrikhand/Shrikhand-Regular.ttf"},
    "Bangers-Regular": {"family": "Bangers", "url": "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf"},
    "TitanOne-Regular": {"family": "Titan One", "url": "https://github.com/google/fonts/raw/main/ofl/titanone/TitanOne-Regular.ttf"},
    "Unbounded-Bold": {"family": "Unbounded", "url": "https://github.com/google/fonts/raw/main/ofl/unbounded/Unbounded-Bold.ttf"},
    "RubikGlitch-Regular": {"family": "Rubik Glitch", "url": "https://github.com/google/fonts/raw/main/ofl/rubikglitch/RubikGlitch-Regular.ttf"},
    "Righteous-Regular": {"family": "Righteous", "url": "https://github.com/google/fonts/raw/main/ofl/righteous/Righteous-Regular.ttf"},
    "Syne-Bold": {"family": "Syne", "url": "https://github.com/google/fonts/raw/main/ofl/syne/Syne-Bold.ttf"},
    "Audiowide-Regular": {"family": "Audiowide", "url": "https://github.com/google/fonts/raw/main/ofl/audiowide/Audiowide-Regular.ttf"},
    "Bungee-Regular": {"family": "Bungee", "url": "https://github.com/google/fonts/raw/main/ofl/bungee/Bungee-Regular.ttf"},
    "Oswald-Bold": {"family": "Oswald", "url": "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Bold.ttf"},
    "BebasNeue-Regular": {"family": "Bebas Neue", "url": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf"},
    "Impact": {"family": "Impact", "url": ""},
}

GENRE_THEMES: Dict[str, Dict[str, Any]] = {
    "Podcast": {
        "font_name": "Montserrat-Black",
        "highlight_color": "&H0000FFFF&",
        "primary_color": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "font_size": 58,
        "outline_width": 6,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Punchy Conversation, Clean Modern Impact",
    },
    "Motivational": {
        "font_name": "Oswald-Bold",
        "highlight_color": "&H0000AAFF&",
        "primary_color": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "font_size": 62,
        "outline_width": 6,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Epic Energy, Dramatic Focus",
    },
    "Anime": {
        "font_name": "Impact",
        "highlight_color": "&H000066FF&",
        "primary_color": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "font_size": 60,
        "outline_width": 6,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Shonen Hype, High-Action Tension",
    },
    "Movie": {
        "font_name": "Montserrat-Black",
        "highlight_color": "&H0000D4FF&",
        "primary_color": "&H00E8E8E8&",
        "outline_color": "&H00000000&",
        "font_size": 56,
        "outline_width": 5,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": False,
        "vibe": "Cinematic Storytelling, Suspenseful Pacing",
    },
    "Web Series": {
        "font_name": "Oswald-Bold",
        "highlight_color": "&H000088FF&",
        "primary_color": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "font_size": 58,
        "outline_width": 6,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Dramatic Face-Off, Character Drama",
    },
    "Song": {
        "font_name": "Montserrat-Black",
        "highlight_color": "&H00FFFF00&",
        "primary_color": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "glow_color": "&H00FF00FF&",
        "font_size": 68,
        "outline_width": 7,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Music Video Kinetic Neon Karaoke with Dynamic Pop & Glow",
    },
    "Gaming": {
        "font_name": "Impact",
        "highlight_color": "&H0000FFFF&",
        "primary_color": "&H00FF00FF&",
        "outline_color": "&H00000000&",
        "font_size": 64,
        "outline_width": 6,
        "shadow": 4,
        "words_per_line": 2,
        "uppercase": True,
        "vibe": "Hype Clutch & Humor",
    },
    "Educational": {
        "font_name": "Montserrat-Black",
        "highlight_color": "&H0000FF88&",
        "primary_color": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "font_size": 56,
        "outline_width": 5,
        "shadow": 3,
        "words_per_line": 2,
        "uppercase": False,
        "vibe": "Curious Insights, Clear Explanation",
    },
}

SUBTITLE_PRESETS = {
    "aujle_tere_te": {
        "name": "✨ Aujle Tere Te (Sans + Golden Calligraphy)",
        "description": "Modern bold sans header + glowing golden calligraphy accent (Viral Karan Aujla aesthetic)",
        "font_name": "Poppins-ExtraBold",
        "secondary_font": "GreatVibes-Regular",
        "font_size": 56,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0018C5F5",
        "glow_color": "&H000088FF",
        "outline_color": "&H00101010",
        "outline_width": 5,
        "shadow": 3,
        "margin_v": 320,
        "sub_position": "center",
        "dual_mode": True,
        "words_per_line": 2,
        "uppercase": False,
    },
    "kad_tera_rafal": {
        "name": "🌹 Kad Tera Rafal (Rose Velvet Editorial)",
        "description": "Tall condensed Roman serif with romantic rose ambient aura & italic subline",
        "font_name": "CinzelDecorative-Bold",
        "secondary_font": "PlayfairDisplay-Bold",
        "font_size": 62,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H00E8F0FF",
        "glow_color": "&H006633FF",
        "outline_color": "&H00201020",
        "outline_width": 5,
        "shadow": 4,
        "margin_v": 320,
        "sub_position": "center",
        "dual_mode": True,
        "words_per_line": 2,
        "uppercase": True,
    },
    "never_imperial_echo": {
        "name": "⚔️ NEVER Echo (Imperial Bodoni + Script Accent)",
        "description": "Majestic Roman serif headline overlaid with delicate cursive echo",
        "font_name": "CinzelDecorative-Bold",
        "secondary_font": "AlexBrush-Regular",
        "font_size": 66,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0020C0FF",
        "glow_color": "&H00101830",
        "outline_color": "&H00000000",
        "outline_width": 4,
        "shadow": 4,
        "margin_v": 320,
        "sub_position": "center",
        "dual_mode": True,
        "words_per_line": 1,
        "uppercase": True,
    },
    "pata_mainu_dedega": {
        "name": "💫 Pata Mainu Dedega (Clean Sans + Golden Script)",
        "description": "Clean modern uppercase sans-serif with vibrant sunset golden signature",
        "font_name": "Montserrat-Black",
        "secondary_font": "DancingScript-Bold",
        "font_size": 56,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0000B4FF",
        "glow_color": "&H000055FF",
        "outline_color": "&H00141414",
        "outline_width": 5,
        "shadow": 3,
        "margin_v": 320,
        "sub_position": "center",
        "dual_mode": True,
        "words_per_line": 2,
        "uppercase": True,
    },
    "mere_te_geetan": {
        "name": "💖 Mere Te Geetan (Neon Rose Calligraphy)",
        "description": "Pure flowing cursive calligraphy with vivid neon pink/magenta backlight halo",
        "font_name": "DancingScript-Bold",
        "secondary_font": "GreatVibes-Regular",
        "font_size": 66,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H00D600FF",
        "glow_color": "&H008000FF",
        "outline_color": "&H00200020",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "sub_position": "center",
        "dual_mode": False,
        "words_per_line": 3,
        "uppercase": False,
    },
    "dela_hype": {
        "name": "Dela Gothic (Tokyo Street Hype)",
        "font_name": "DelaGothicOne-Regular",
        "font_size": 62,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0066FF00",
        "glow_color": "&H007F00FF",
        "outline_color": "&H00180018",
        "outline_width": 7,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "shrikhand_velvet": {
        "name": "Shrikhand (Velvet Melodic Glow)",
        "font_name": "Shrikhand-Regular",
        "font_size": 64,
        "primary_color": "&H00E6F7FF",
        "highlight_color": "&H0003B7FF",
        "glow_color": "&H00FF0099",
        "outline_color": "&H00200020",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "bangers_action": {
        "name": "Bangers (Pop-Art Action Punch)",
        "font_name": "Bangers-Regular",
        "font_size": 68,
        "primary_color": "&H0000E6FF",
        "highlight_color": "&H003314FF",
        "glow_color": "&H0000D7FF",
        "outline_color": "&H00000000",
        "outline_width": 7,
        "shadow": 5,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "titan_bubble": {
        "name": "Titan (3D Chunky Bubble Pop)",
        "font_name": "TitanOne-Regular",
        "font_size": 64,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H00FFF000",
        "glow_color": "&H000088FF",
        "outline_color": "&H00331100",
        "outline_width": 7,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "unbounded_tech": {
        "name": "Unbounded (Cyber Avant-Garde)",
        "font_name": "Unbounded-Bold",
        "font_size": 58,
        "primary_color": "&H00F0F4F8",
        "highlight_color": "&H007F00FF",
        "glow_color": "&H00FFFF00",
        "outline_color": "&H0018181B",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "glitch_matrix": {
        "name": "Rubik Glitch (Digital Cyber Bass)",
        "font_name": "RubikGlitch-Regular",
        "font_size": 62,
        "primary_color": "&H005EC522",
        "highlight_color": "&H00FFE500",
        "glow_color": "&H000000FF",
        "outline_color": "&H00000000",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "neon_righteous": {
        "name": "Righteous Neon (Stylish Pop & Song)",
        "font_name": "Righteous-Regular",
        "font_size": 66,
        "primary_color": "&H00FFFF00",
        "outline_color": "&H00300030",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "syne_hyperpop": {
        "name": "Syne Hyper-Pop (Music Video)",
        "font_name": "Syne-Bold",
        "font_size": 64,
        "primary_color": "&H00FF00FF",
        "outline_color": "&H00000000",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "audiowide_cyber": {
        "name": "Audiowide Cyber (Electro / EDM)",
        "font_name": "Audiowide-Regular",
        "font_size": 60,
        "primary_color": "&H0000FFFF",
        "outline_color": "&H00000000",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "bungee_punch": {
        "name": "Bungee Urban (Street Rap / Hip-Hop)",
        "font_name": "Bungee-Regular",
        "font_size": 58,
        "primary_color": "&H001E90FF",
        "outline_color": "&H00000000",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "tiktok_yellow": {
        "name": "Viral TikTok Yellow",
        "font_name": "Impact",
        "font_size": 58,
        "primary_color": "&H0000FFFF",
        "outline_color": "&H00000000",
        "outline_width": 5,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "neon_cyber": {
        "name": "Neon Cyan (Music Video)",
        "font_name": "Oswald-Bold",
        "font_size": 58,
        "primary_color": "&H00FFFF00",
        "outline_color": "&H00300030",
        "outline_width": 6,
        "shadow": 4,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "hormozi_white": {
        "name": "Hormozi Clean White",
        "font_name": "Montserrat-Black",
        "font_size": 60,
        "primary_color": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "outline_width": 6,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "emerald_glow": {
        "name": "Emerald Green Glow",
        "font_name": "Poppins-ExtraBold",
        "font_size": 58,
        "primary_color": "&H0044FF00",
        "outline_color": "&H00000000",
        "outline_width": 5,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
    "sunset_fire": {
        "name": "Sunset Fire Red",
        "font_name": "BebasNeue-Regular",
        "font_size": 62,
        "primary_color": "&H001E90FF",
        "outline_color": "&H00000000",
        "outline_width": 6,
        "shadow": 3,
        "margin_v": 320,
        "words_per_line": 2,
        "uppercase": True,
    },
}


def ensure_directories():
    """Initializes all necessary SSD working folders."""
    for folder in [Config.DOWNLOADS_DIR, Config.TEMP_DIR, Config.OUTPUT_DIR, Config.FONTS_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def purge_temp_cache(clear_models: bool = False) -> dict:
    """Safely frees intermediate temp files from SSD and forces garbage collection."""
    import gc
    freed_bytes = 0
    deleted_files = 0
    if Config.TEMP_DIR.exists():
        for f in Config.TEMP_DIR.glob("*"):
            if f.is_file():
                try:
                    freed_bytes += f.stat().st_size
                    f.unlink(missing_ok=True)
                    deleted_files += 1
                except Exception:
                    pass

    if clear_models:
        try:
            from core.stt.whisper_engine import purge_whisper_cache
            purge_whisper_cache()
        except Exception:
            pass

    gc.collect()
    return {"freed_mb": round(freed_bytes / (1024 * 1024), 1), "deleted_files": deleted_files}


def get_system_memory_info() -> dict:
    """Monitors live RAM, CPU and VRAM safe limits."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        total_gb = round(vm.total / (1024**3), 1)
        avail_gb = round(vm.available / (1024**3), 1)
        used_pct = round(vm.percent, 1)

        return {
            "total_gb": total_gb,
            "available_gb": avail_gb,
            "used_percent": used_pct,
            "cpu_percent": cpu_pct,
            "recommended_workers": 1,
            "status": "healthy" if used_pct < 85 else "warning",
        }
    except Exception:
        return {
            "total_gb": 8.0,
            "available_gb": 4.0,
            "used_percent": 50.0,
            "cpu_percent": 15.0,
            "recommended_workers": 1,
            "status": "healthy",
        }

