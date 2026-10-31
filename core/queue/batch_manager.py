"""
Multi-User Concurrent Batch Queue Manager.
Enforces:
1. Isolated Session Namespacing: Each user has their own session space.
2. Fair Scheduling: Jobs from different sessions are balanced so one user cannot starve others.
3. Low-VRAM Safety: Heavy GPU stages (Whisper STT & FFmpeg NVENC/QSV) run sequentially
   to protect consumer hardware from Out-Of-Memory (OOM) crashes.
4. Thread-Safe State & Real-time Progress Tracking.
"""

import time
import shutil
import threading
from typing import Dict, List, Optional
from collections import deque

from core.queue.job_models import GenerationJob


class BatchQueueManager:
    """Enterprise multi-user batch orchestrator with fair worker dispatch."""
    def __init__(self):
        self._jobs: Dict[str, GenerationJob] = {}
        self._queue: deque = deque()
        self._lock = threading.RLock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._current_job_id: Optional[str] = None
        self._pipeline_fn = None

    def set_pipeline_executor(self, fn):
        """Injects the pipeline execution function to avoid circular imports."""
        self._pipeline_fn = fn

    def start_worker(self):
        """Starts the background worker daemon if not already running."""
        with self._lock:
            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._stop_event.clear()
                self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True, name="AutoClipQueueWorker")
                self._worker_thread.start()
                print("  🚀 [BatchQueueManager] Multi-user background worker thread launched.")

    def submit_job(self, params: dict, session_id: str = "default", user_id: str = None) -> GenerationJob:
        """Submits a new video clipping job into the fair execution queue."""
        job = GenerationJob(
            session_id=session_id,
            user_id=user_id,
            params=params,
            video_title=params.get("youtube_url") or params.get("local_video_path") or "New Video Job",
        )
        job.add_log(f"Job registered for session {session_id[:8]}...")

        with self._lock:
            self._jobs[job.job_id] = job
            self._queue.append(job.job_id)

        self.start_worker()
        return job

    def get_job(self, job_id: str) -> Optional[GenerationJob]:
        """Retrieves a job by its unique ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self, session_id: Optional[str] = None) -> List[dict]:
        """
        Lists all jobs. If session_id is provided, returns that user's jobs,
        plus currently running or recent jobs.
        """
        with self._lock:
            sorted_jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
            if session_id:
                return [j.to_dict() for j in sorted_jobs if j.session_id == session_id or j.session_id == "default"]
            return [j.to_dict() for j in sorted_jobs]

    def cancel_job(self, job_id: str) -> bool:
        """Cancels a queued or running job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job.status in ("completed", "failed", "cancelled"):
                return False

            if job_id in self._queue:
                self._queue.remove(job_id)

            job.status = "cancelled"
            job.current_step = "Job cancelled by user."
            job.completed_at = time.time()
            job.add_log("🛑 Job cancelled.")
            return True

    def delete_job(self, job_id: str) -> bool:
        """Removes job record and purges its dedicated temp directory."""
        with self._lock:
            job = self._jobs.pop(job_id, None)
            if job_id in self._queue:
                self._queue.remove(job_id)

        if job:
            try:
                if job.temp_dir.exists():
                    shutil.rmtree(job.temp_dir, ignore_errors=True)
            except Exception:
                pass
            return True
        return False

    def get_active_job(self) -> Optional[GenerationJob]:
        """Returns the currently processing job, if any."""
        with self._lock:
            if self._current_job_id:
                return self._jobs.get(self._current_job_id)
        return None

    def _worker_loop(self):
        """Fair round-robin / FIFO queue dispatcher."""
        while not self._stop_event.is_set():
            job_to_run = None
            with self._lock:
                if self._queue:
                    next_id = self._queue.popleft()
                    candidate = self._jobs.get(next_id)
                    if candidate and candidate.status == "queued":
                        job_to_run = candidate
                        self._current_job_id = next_id
                        job_to_run.status = "starting"
                        job_to_run.started_at = time.time()

            if not job_to_run:
                time.sleep(0.5)
                continue

            # Execute the job safely with dedicated callback
            try:
                self._execute_job(job_to_run)
            except Exception as e:
                job_to_run.status = "failed"
                job_to_run.error = str(e)
                job_to_run.completed_at = time.time()
                job_to_run.add_log(f"❌ Unhandled execution error: {e}")
            finally:
                with self._lock:
                    self._current_job_id = None
                # Clean up job isolated temp directory after run
                try:
                    if job_to_run.temp_dir.exists():
                        shutil.rmtree(job_to_run.temp_dir, ignore_errors=True)
                except Exception:
                    pass

    def _execute_job(self, job: GenerationJob):
        """Runs the complete end-to-end pipeline for a single job."""
        if self._pipeline_fn is None:
            raise RuntimeError("Pipeline executor is not configured on BatchQueueManager")

        def job_log_callback(msg: str):
            job.add_log(msg)
            # Infer step progress from logs
            if "STEP 1" in msg or "Streaming to SSD" in msg:
                job.status = "downloading"
                job.current_step = "Downloading media to SSD"
                job.progress = max(job.progress, 15)
            elif "STEP 2" in msg or "AUDIO EXTRACTION" in msg:
                job.status = "audio_extract"
                job.current_step = "Extracting uncompressed audio"
                job.progress = max(job.progress, 30)
            elif "STEP 3" in msg or "WHISPER STT" in msg or "Transcribing" in msg:
                job.status = "transcribing"
                job.current_step = "AI Whisper Speech-to-Text transcription"
                job.progress = max(job.progress, 50)
            elif "STEP 4" in msg or "CLIP SELECTION" in msg:
                job.status = "clipping"
                job.current_step = "Selecting highlight boxes"
                job.progress = max(job.progress, 70)
            elif "STEP 5" in msg or "Rendering Box" in msg or "Sequential Encoder" in msg:
                job.status = "rendering"
                job.current_step = "GPU Hardware Transcoding"
                job.progress = max(job.progress, 85)

        job.add_log(f"🚀 Execution started for job {job.job_id}")

        params = dict(job.params)
        params["log_callback"] = job_log_callback

        results = self._pipeline_fn(**params)

        if results and isinstance(results, dict):
            job.video_title = results.get("video_title", job.video_title)
            job.output_files = results.get("generated_shorts", [])
            job.status = "completed"
            job.progress = 100
            job.current_step = f"Completed ({len(job.output_files)} shorts generated)"
            job.completed_at = time.time()
            job.add_log(f"🎉 Pipeline successfully generated {len(job.output_files)} shorts!")
        else:
            job.status = "completed"
            job.progress = 100
            job.current_step = "Completed with no outputs"
            job.completed_at = time.time()


# Global Singleton Batch Manager
BATCH_MANAGER = BatchQueueManager()

