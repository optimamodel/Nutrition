import os
import multiprocessing as mp
from pathlib import Path

def _cpus_from_cgroup_v2():
    """Return integer CPUs from cgroup v2 cpu.max, or None if unavailable."""
    try:
        q, p = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if q != "max":
            # cpu.max: "<quota> <period>"
            q, p = int(q), int(p)
            if p > 0:
                return max(1, q // p)
    except Exception:
        pass
    return None

def _cpus_from_cgroup_v1():
    """Return integer CPUs from cgroup v1 cpu.cfs_* files, or None if unavailable."""
    try:
        q = int(Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us").read_text())
        p = int(Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us").read_text())
        if q > 0 and p > 0:
            return max(1, q // p)
    except Exception:
        pass
    return None

def _effective_cpus():
    """Best-effort effective CPU count (container-aware), falling back to host."""
    # Explicit override first
    if "WEB_CONCURRENCY" in os.environ:
        try:
            n = int(os.environ["WEB_CONCURRENCY"])
            if n > 0:
                return n
        except ValueError:
            pass

    # Workers per core override (e.g., set WORKERS_PER_CORE=2 for CPU-bound workloads)
    wpc = float(os.getenv("WORKERS_PER_CORE", "1").strip() or "1")

    # Container quotas (v2 then v1)
    n = _cpus_from_cgroup_v2()
    if n is None:
        n = _cpus_from_cgroup_v1()
    if n is None:
        n = mp.cpu_count()

    # Cap/adjust via optional limits
    max_workers = int(os.getenv("MAX_WORKERS", "0"))  # 0 = no cap
    computed = max(1, int(n * wpc))
    if max_workers > 0:
        computed = min(computed, max_workers)
    return computed

timeout =180
workers = _effective_cpus()
bind = "127.0.0.1:9101"

