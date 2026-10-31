import time
from typing import Dict, Any, List

class HarmonicPipelinePacer:
    """Metabolic pacing between heavy GPU transcode and CPU Whisper tasks."""
    STAGE_COOLDOWNS = {
        ("download", "stt"):    0.05,
        ("stt", "clipping"):    0.05,
        ("clipping", "render"): 0.15,
        ("render", "render"):   0.10,
    }

    def pace_transition(self, prev_stage: str, next_stage: str):
        sleep_sec = self.STAGE_COOLDOWNS.get((prev_stage, next_stage), 0.05)
        if sleep_sec > 0:
            time.sleep(sleep_sec)

class LeastActionGeodesic:
    """Action potential logger tracking pipeline duration and file size records."""
    def __init__(self):
        self._action_records: List[Dict[str, Any]] = []

    def log_action(self, action_name: str, duration_sec: float, bytes_processed: int):
        self._action_records.append({
            "action": action_name,
            "duration_sec": round(duration_sec, 3),
            "mb": round(bytes_processed / (1024 * 1024), 2),
            "timestamp": time.time()
        })

    def get_efficiency_summary(self) -> Dict[str, Any]:
        return {
            "total_stages": len(self._action_records),
            "records": self._action_records[-10:]
        }


PACER = HarmonicPipelinePacer()
GEODESIC = LeastActionGeodesic()

