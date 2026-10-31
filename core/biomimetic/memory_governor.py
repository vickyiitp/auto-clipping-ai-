import gc
import psutil
from typing import Dict, Any

class LaminarMemoryGovernor:
    """
    Maintains laminar data flow through memory. Monitors available RAM and
    dynamically modulates processing pressure so consumer laptops NEVER crash.
    """
    CRITICAL_RAM_MB = 1200  # If free RAM drops below 1.2 GB, trigger soft pause & GC
    WARNING_RAM_MB  = 2000  # If free RAM drops below 2.0 GB, restrict concurrent I/O

    @classmethod
    def get_memory_state(cls) -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        avail_mb = vm.available / (1024 * 1024)
        return {
            "available_mb": round(avail_mb, 1),
            "available_gb": round(avail_mb / 1024, 2),
            "total_gb": round(vm.total / (1024 * 1024 * 1024), 1),
            "used_pct": vm.percent,
            "is_critical": avail_mb < cls.CRITICAL_RAM_MB,
            "is_warning": avail_mb < cls.WARNING_RAM_MB,
        }

    @classmethod
    def guard_memory_pressure(cls, log_callback=None):
        """Forces garbage collection if available memory drops into the warning threshold."""
        state = cls.get_memory_state()
        if state["is_critical"]:
            if log_callback:
                log_callback(f"  🌊 [Laminar Governor] Critical RAM alert: {state['available_mb']}MB free. Purging cache...")
            gc.collect()
        elif state["is_warning"]:
            gc.collect()

