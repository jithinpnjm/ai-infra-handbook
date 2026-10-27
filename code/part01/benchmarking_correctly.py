"""Chapter 1.25 model: Sanity-check bandwidth arithmetic (IOPS x block size vs
link capacity), NCCL all-reduce algorithm bandwidth (algbw) to bus bandwidth
(busbw = algbw * 2*(n-1)/n) conversion, benchmark paradox probability, and
median/MAD regression gating.

Sources modeled:
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 12 ("Benchmarking": 16 benchmarking failures, micro/macro/replay/industry
  types, active benchmarking, Bonnie++ 739 KB/s 1-byte vfs_write analysis,
  50,000 NFS IOPS x 8 KiB = 3.2 Gbit/s > 1 GbE sanity check, 6-question checklist).
"""
import statistics
from typing import Dict, List


SIX_CHECKLIST_QUESTIONS: List[str] = [
    "1_why_not_double",
    "2_did_it_break_limits",
    "3_did_it_error",
    "4_does_it_reproduce",
    "5_does_it_matter",
    "6_did_it_even_happen",
]


def check_iops_link_sanity(
    claimed_iops: int,
    io_size_bytes: int,
    link_rate_gbps: float,
) -> Dict[str, object]:
    """Verify whether claimed_iops at io_size_bytes is physically possible over link_rate_gbps."""
    if claimed_iops < 0 or io_size_bytes <= 0 or link_rate_gbps <= 0:
        raise ValueError("Invalid sanity-check parameters")
    bytes_per_sec = claimed_iops * io_size_bytes
    required_gbps = round((bytes_per_sec * 8.0) / 1e9, 3)
    possible = required_gbps <= link_rate_gbps
    return {
        "required_gbps": required_gbps,
        "link_rate_gbps": link_rate_gbps,
        "physically_possible_on_wire": possible,
    }


def compute_nccl_allreduce_busbw(
    size_bytes: int,
    time_sec: float,
    num_ranks: int,
) -> Dict[str, float]:
    """Compute nccl-tests algbw (GB/s) and busbw = algbw * 2*(n - 1)/n (GB/s) for AllReduce."""
    if size_bytes <= 0 or time_sec <= 0 or num_ranks < 2:
        raise ValueError("size_bytes > 0, time_sec > 0, and num_ranks >= 2 required")
    algbw_gbs = (size_bytes / time_sec) / 1e9
    factor = (2.0 * (num_ranks - 1)) / float(num_ranks)
    busbw_gbs = algbw_gbs * factor
    return {
        "algbw_gbs": round(algbw_gbs, 2),
        "factor": round(factor, 4),
        "busbw_gbs": round(busbw_gbs, 2),
    }


def compute_benchmark_paradox_win_prob(single_win_prob: float, num_benchmarks: int) -> float:
    """Compute probability of winning all num_benchmarks independent tests (e.g. 0.5^3 = 0.125)."""
    if not (0.0 <= single_win_prob <= 1.0) or num_benchmarks < 1:
        raise ValueError("Invalid probability or count")
    return round(single_win_prob ** num_benchmarks, 4)


def evaluate_median_mad_regression_gate(
    baseline_samples: List[float],
    candidate_samples: List[float],
    k_mad: float = 3.0,
) -> Dict[str, object]:
    """Compare candidate median against baseline_median - k_mad * MAD (higher metric = better)."""
    if not baseline_samples or not candidate_samples:
        raise ValueError("Sample lists must be non-empty")
    base_med = float(statistics.median(baseline_samples))
    mad = float(statistics.median([abs(x - base_med) for x in baseline_samples]))
    threshold = round(base_med - k_mad * mad, 3)
    cand_med = float(statistics.median(candidate_samples))
    return {
        "baseline_median": round(base_med, 3),
        "baseline_mad": round(mad, 3),
        "threshold": threshold,
        "candidate_median": round(cand_med, 3),
        "passed": cand_med >= threshold,
    }
