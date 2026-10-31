import time
from typing import Dict, Any, List, Tuple

class ResilientRouteMesh:
    """
    Self-Healing 10-Route Dynamic Mesh:
    If any single route encounters an error (hardware driver crash, missing model,
    network drop, font mismatch, corrupt frame), work NEVER halts. The mesh
    instantly and autonomously reroutes to the next tier in the chain.
    """
    ROUTES_CATALOG = {
        "R1_INGESTION": {
            "name": "Video Ingestion Mesh",
            "tiers": ["Tier 1: 1080p Split-Merge", "Tier 2: Direct Single Container", "Tier 3: Local Cached Stream"]
        },
        "R2_VOCAL_EXTRACT": {
            "name": "Vocal Extraction Mesh",
            "tiers": ["Tier 1: 4-Pole Vocal Bandpass (0.3s)", "Tier 2: Standard Mono 16kHz Resampling", "Tier 3: Direct Stream Passthrough"]
        },
        "R3_STT_TRANSCRIBE": {
            "name": "Speech-to-Text Mesh",
            "tiers": ["Tier 1: P-Core Faster-Whisper Model", "Tier 2: Batched Inference Pipeline", "Tier 3: Unfiltered Robust Passthrough"]
        },
        "R4_SUBJECT_FRAMING": {
            "name": "NASA Kalman 9:16 Subject Framing",
            "tiers": ["Tier 1: 1D Kalman + Predictive Delta", "Tier 2: Proxy Weighted Average", "Tier 3: Cinematic Center Crop"]
        },
        "R5_AI_HIGHLIGHTS": {
            "name": "AI Highlight Selection Mesh",
            "tiers": ["Tier 1: Ollama Llama-3.1 Structured", "Tier 2: Phonetic Speech-Density", "Tier 3: Golden-Ratio Uniform"]
        },
        "R6_HW_TRANSCODE": {
            "name": "Hardware Transcoding Mesh",
            "tiers": ["Tier 1: Intel Quick Sync (h264_qsv)", "Tier 2: Multi-Threaded libx264", "Tier 3: Safe Video Crop Render"]
        },
        "R7_KINETIC_TYPO": {
            "name": "Kinetic Typography Mesh",
            "tiers": ["Tier 1: Dual-Font Glow Calligraphy", "Tier 2: High-Contrast Bold Sans", "Tier 3: Safe Standard ASS"]
        },
        "R8_TRANSLITERATION": {
            "name": "Sing-Along Transliteration Mesh",
            "tiers": ["Tier 1: AnyAscii Phonetic Romanization", "Tier 2: Regex ASCII Sanitization", "Tier 3: Raw Passthrough"]
        },
        "R9_LAMINAR_GOVERNOR": {
            "name": "Memory & Thermal Protection Mesh",
            "tiers": ["Tier 1: Laminar Micro-Glide", "Tier 2: Emergency SSD Temp Purge", "Tier 3: Micro-Chunk Segmentation"]
        },
        "R10_BATCH_PIPELINE": {
            "name": "Multi-URL Batch Pipeline Mesh",
            "tiers": ["Tier 1: Pipelined Background Pre-Loader", "Tier 2: Isolated Job Circuit Breaker", "Tier 3: Auto-Reconnecting Polling"]
        }
    }

    def __init__(self):
        self.reroute_history: List[Dict[str, Any]] = []

    def execute(self, route_id: str, tiers: List[Tuple[str, Any]], log_callback=None):
        """
        Executes a sequence of fallback callable tiers for a route.
        If Tier N fails, catches the exception, logs the dynamic reroute,
        and proceeds to Tier N+1 without stopping the job.
        """
        def safe_log(msg: str):
            if not log_callback:
                return
            try:
                log_callback(msg)
            except UnicodeEncodeError:
                try:
                    log_callback(msg.encode("ascii", errors="replace").decode("ascii"))
                except Exception:
                    pass
            except Exception:
                pass

        last_error = None
        for tier_idx, (tier_name, tier_func) in enumerate(tiers, 1):
            try:
                result = tier_func()
                if tier_idx > 1:
                    safe_log(f"  [Route Mesh] {route_id} recovered successfully on {tier_name}!")
                return result
            except Exception as e:
                last_error = e
                event = {
                    "route": route_id,
                    "failed_tier": tier_name,
                    "error": str(e),
                    "timestamp": time.time()
                }
                self.reroute_history.append(event)
                safe_log(f"  [Route Mesh] {route_id} {tier_name} bypassed ({e}). Auto-rerouting to next tier...")

        raise RuntimeError(f"All tiers exhausted for route {route_id}. Last failure: {last_error}")

    def get_mesh_status(self) -> Dict[str, Any]:
        return {
            "total_routes": len(self.ROUTES_CATALOG),
            "routes": {
                r_id: {
                    "name": data["name"],
                    "tiers": " ".join(data["tiers"])
                }
                for r_id, data in self.ROUTES_CATALOG.items()
            },
            "recent_reroutes": self.reroute_history[-5:],
            "reroute_events_count": len(self.reroute_history)
        }

ROUTE_MESH = ResilientRouteMesh()

