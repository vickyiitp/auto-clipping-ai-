"""
Genre Prompts & Ollama LLM Schema for Viral Clip Selection.
"""

import json
import urllib.request
from typing import List
from pydantic import BaseModel, Field
from core.config import Config

OLLAMA_AVAILABLE = False
try:
    from ollama import chat
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


GENRE_CRITERIA_MAP = {
    "Podcast": (
        "Focus on conversational hooks, provocative claims, counter-intuitive debates, "
        "and punchy dialogue exchanges between speakers. Prioritize strong first-3-second statements."
    ),
    "Motivational": (
        "Focus on high-energy emotional breakthroughs, mindset shifts, life lessons, "
        "discipline/hustle philosophy, and turning-point statements that inspire the viewer."
    ),
    "Anime": (
        "Focus on high-stakes narrative tension, battle climaxes, emotional power awakenings, "
        "or iconic hype punchlines with maximum dramatic intensity."
    ),
    "Movie": (
        "Focus on intense suspenseful scenes, shocking plot revelations, high-stakes confrontation dialogue, "
        "or comedic turning points that create natural cliffhangers."
    ),
    "Web Series": (
        "Focus on dramatic character clashes, secret exposes, high-tension face-offs, "
        "and cliffhanger moments that demand part 2."
    ),
    "Song": (
        "Focus on peak vocal choruses, energy drops, rhythmic lyric hooks, "
        "and the most memorable emotional melody segments."
    ),
    "Gaming": (
        "Focus on clutch gameplay moments, high-pitch reaction rage/hype, "
        "hilarious fails, and energetic commentary punchlines."
    ),
    "Educational": (
        "Focus on fascinating 'Did You Know?' facts, rapid tutorials, mind-blowing explanations, "
        "and problem-solution reveals that keep viewers hooked."
    ),
}


class LLMClipItem(BaseModel):
    title: str = Field(description="Punchy, catchy short title for this viral clip")
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    reason: str = Field(description="Why this segment fits the genre and hooks the audience")
    hook_score: int = Field(description="Predicted viral retention score from 1 to 10")


class LLMClipResponse(BaseModel):
    clips: List[LLMClipItem] = Field(description="List of best viral clip candidates")


def check_ollama() -> bool:
    """Checks if Ollama service is running AND requested model is installed."""
    global OLLAMA_AVAILABLE
    if not OLLAMA_AVAILABLE:
        return False
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                model_base = Config.OLLAMA_MODEL.split(":")[0]
                return model_base in models
    except Exception:
        pass
    return False

