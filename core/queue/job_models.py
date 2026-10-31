"""
Job Models for Multi-User Concurrent Batch Execution.
Defines thread-safe job metadata, status enumerations, and isolated resource namespaces.
"""

import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from core.config import Config


@dataclass
class GenerationJob:
    """Enterprise multi-user generation job state container."""
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    session_id: str = "default"
    user_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    # Pipeline parameters
    params: Dict[str, Any] = field(default_factory=dict)
    video_title: str = "Pending Video"

    # Live Execution State
    status: str = "queued"  # queued, downloading, transcribing, clipping, rendering, completed, failed, cancelled
    progress: int = 0
    current_step: str = "Waiting in queue..."
    error: Optional[str] = None

    # Logs & Outputs
    logs: List[str] = field(default_factory=list)
    output_files: List[Dict[str, Any]] = field(default_factory=list)

    # Per-Job Isolated Temp Storage
    temp_dir_name: str = field(default_factory=lambda: f"job_{uuid.uuid4().hex[:8]}")

    @property
    def temp_dir(self) -> Path:
        p = Config.TEMP_DIR / self.temp_dir_name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def add_log(self, message: str):
        """Appends a timestamped log to the job's ring buffer."""
        ts = time.strftime("[%H:%M:%S]")
        formatted = f"{ts} {message}"
        self.logs.append(formatted)
        if len(self.logs) > 600:
            self.logs.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes job representation for JSON REST API."""
        return {
            "job_id": self.job_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "video_title": self.video_title,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "error": self.error,
            "output_files": self.output_files,
            "log_count": len(self.logs),
            "recent_logs": self.logs[-25:],
        }

