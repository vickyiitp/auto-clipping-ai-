import os
import psutil
from contextlib import contextmanager
from typing import List, Optional

class HardwareTopology:
    """Discovers CPU topology (P-Cores vs E-Cores on Intel Hybrid, or Zen on AMD)."""
    def __init__(self):
        self.logical_cores = psutil.cpu_count(logical=True) or 4
        self.physical_cores = psutil.cpu_count(logical=False) or 4
        self.is_hybrid_intel = (self.logical_cores > self.physical_cores and self.physical_cores >= 6)
        
        self.p_core_threads: List[int] = []
        self.e_core_threads: List[int] = []
        
        if self.is_hybrid_intel:
            # Intel Core i7/i9: 6 P-cores (12 threads: 0-11) + E-cores (threads 12-15)
            p_core_count = max(4, min(8, self.physical_cores - 4))
            p_threads_count = p_core_count * 2
            self.p_core_threads = list(range(0, min(p_threads_count, self.logical_cores)))
            self.e_core_threads = list(range(min(p_threads_count, self.logical_cores), self.logical_cores))
        else:
            self.p_core_threads = list(range(self.logical_cores))
            self.e_core_threads = []

        self.optimal_stt_threads = min(8, max(4, len(self.p_core_threads) // 2 or 4))

    def get_summary(self) -> dict:
        return {
            "logical_cores": self.logical_cores,
            "physical_cores": self.physical_cores,
            "is_hybrid_intel": self.is_hybrid_intel,
            "p_core_threads": len(self.p_core_threads),
            "e_core_threads": len(self.e_core_threads),
            "optimal_stt_threads": self.optimal_stt_threads,
        }

TOPOLOGY = HardwareTopology()

@contextmanager
def starling_affinity_lock(mode: str = "p_cores"):
    """
    Context manager that temporarily locks the calling process/thread to
    high-speed Performance Cores during heavy AI tensor matrix operations.
    """
    proc = psutil.Process()
    orig_affinity = None
    try:
        if hasattr(proc, "cpu_affinity"):
            orig_affinity = proc.cpu_affinity()
            if mode == "p_cores" and TOPOLOGY.p_core_threads:
                proc.cpu_affinity(TOPOLOGY.p_core_threads)
            elif mode == "e_cores" and TOPOLOGY.e_core_threads:
                proc.cpu_affinity(TOPOLOGY.e_core_threads)
    except Exception:
        pass

    try:
        yield
    finally:
        if orig_affinity is not None:
            try:
                proc.cpu_affinity(orig_affinity)
            except Exception:
                pass
