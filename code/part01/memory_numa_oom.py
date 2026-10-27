"""Chapter 1.17 model: TLB reach calculation (4 KiB vs 2 MiB vs 1 GiB huge pages),
PSS/RSS/USS shared-memory accounting, Linux page-reclaim watermark calculation
(min, low, high from min_free_kbytes and watermark_scale_factor), OOM badness
scoring with oom_score_adj, and training-node host RAM capacity budgeting.

Sources modeled:
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 7 ("Memory": virtual memory, paging, demand paging, overcommit,
  TLB reach, slab/SLUB magazines [Bonwick 94/01], kswapd watermarks, OOM killer,
  PSI, vmstat/sar/slabtop/numastat/pmap/drsnoop/wss/bpftrace).
- nvidia-devops/volume-01/01-linux-compute-memory-masterclass.md (NUMA GPU trap,
  TLB reach, watermarks, OOM score mechanics, pinned host memory).
"""
from typing import Dict, List


def compute_tlb_reach_bytes(num_entries: int, page_size_bytes: int) -> Dict[str, float]:
    """Compute the TLB coverage ('reach') in bytes and MiB for a given entry count and page size."""
    if num_entries <= 0 or page_size_bytes <= 0:
        raise ValueError("num_entries and page_size_bytes must be positive")
    reach_bytes = num_entries * page_size_bytes
    return {
        "entries": num_entries,
        "page_size_bytes": page_size_bytes,
        "reach_bytes": reach_bytes,
        "reach_mib": round(reach_bytes / float(1 << 20), 3),
    }


def compute_process_memory_accounting(
    private_kib: int,
    shared_kib: int,
    num_sharing_processes: int,
) -> Dict[str, int]:
    """Compute USS, PSS, and RSS (in KiB) for a process sharing shared_kib across num_sharing_processes."""
    if private_kib < 0 or shared_kib < 0 or num_sharing_processes <= 0:
        raise ValueError("Invalid memory accounting parameters")
    uss = private_kib
    rss = private_kib + shared_kib
    pss = private_kib + (shared_kib // num_sharing_processes)
    return {"uss_kib": uss, "pss_kib": pss, "rss_kib": rss}


def compute_zone_watermarks_kib(
    total_ram_kib: int,
    min_free_kib: int,
    watermark_scale_factor: int = 10,
) -> Dict[str, int]:
    """Compute min, low, and high zone watermarks (in KiB).
    watermark_scale_factor is in units of 1/10,000 of total RAM (default 10 = 0.1%).
    """
    if total_ram_kib <= 0 or min_free_kib <= 0 or watermark_scale_factor <= 0:
        raise ValueError("Watermark parameters must be positive")
    step = max(min_free_kib // 4, int(total_ram_kib * watermark_scale_factor // 10000))
    w_min = min_free_kib
    w_low = w_min + step
    w_high = w_min + 2 * step
    return {"min_kib": w_min, "low_kib": w_low, "high_kib": w_high, "step_kib": step}


def compute_oom_effective_score(rss_Plus_swap_kib: int, total_ram_plus_swap_kib: int, oom_score_adj: int = 0) -> int:
    """Compute Linux OOM badness score in [0, 1000] given memory footprint and oom_score_adj [-1000, 1000]."""
    if total_ram_plus_swap_kib <= 0 or not (-1000 <= oom_score_adj <= 1000):
        raise ValueError("Invalid OOM score parameters")
    if oom_score_adj == -1000:
        return 0
    base = int(round(1000.0 * rss_Plus_swap_kib / total_ram_plus_swap_kib))
    score = base + oom_score_adj
    return max(1, min(1000, score))


def audit_training_node_ram_budget(
    total_ram_gib: float,
    num_gpus: int,
    workers_per_gpu: int,
    gb_per_worker: float,
    pinned_buffers_gib: float,
    os_and_daemons_gib: float = 16.0,
) -> Dict[str, object]:
    """Calculate total host RAM required by an 8-GPU training node and check whether it fits."""
    if total_ram_gib <= 0 or num_gpus <= 0 or workers_per_gpu < 0 or gb_per_worker < 0:
        raise ValueError("Invalid node budget parameters")
    workers_gib = num_gpus * workers_per_gpu * gb_per_worker
    required_gib = os_and_daemons_gib + workers_gib + pinned_buffers_gib
    remaining_for_cache_gib = round(total_ram_gib - required_gib, 2)
    return {
        "workers_total_gib": round(workers_gib, 2),
        "required_gib": round(required_gib, 2),
        "remaining_for_cache_gib": remaining_for_cache_gib,
        "fits_in_ram": remaining_for_cache_gib >= 0.0,
    }
