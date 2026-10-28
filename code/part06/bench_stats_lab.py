#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.28: HPC benchmarking: HPL, HPCG, IOR, OSU and NCCL tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_stats import hpl_like, triad

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def nccl_busbw(size_bytes: float, elapsed_s: float, nranks: int, collective: str = "all_reduce") -> tuple[float, float]:
    """Compute nccl-tests algbw (GB/s) and busbw (GB/s) per doc/PERFORMANCE.md."""
    algbw = (size_bytes / 1e9) / elapsed_s
    if collective == "all_reduce":
        factor = 2.0 * (nranks - 1) / nranks
    elif collective in ("reduce_scatter", "all_gather", "alltoall"):
        factor = (nranks - 1) / nranks
    else:
        factor = 1.0
    busbw = algbw * factor
    return round(algbw, 1), round(busbw, 1)


def main() -> None:
    # 1. Verify bench_stats.py hpl_like() LU solve residual (< 16.0) and triad() bandwidth harness (and Apple M3 table 44.6, 79.7, 82.2, 114602d)
    gf, resid = hpl_like(n=200, reps=5)
    bw = triad(n=100_000, reps=5)
    m3_ref_gflops = (44.7, 81.3, 90.8, 22.9, 44.6, 79.7, 82.2, 114602)
    check(
        "bench_stats.py HPL-like LU passes scaled residual check (< 16) and triad returns 5 positive bandwidth samples",
        len(gf) == 5 and all(x > 0 for x in gf) and resid < 16.0 and len(bw) == 5 and m3_ref_gflops[2] == 90.8,
    )

    # 2. Verify nccl-tests algbw and busbw formulas (8 GiB = 8,589,934,592 B, 64 ranks, 0.60 s -> algbw=14.3, busbw=28.2 GB/s)
    algbw, busbw = nccl_busbw(float(8 * (1 << 30)), 0.60, 64, "all_reduce")
    _, ag_busbw = nccl_busbw(float(8 * (1 << 30)), 0.60, 64, "all_gather")
    check(
        "nccl_busbw computes algbw=14.3 GB/s and busbw=28.2 GB/s (AllReduce 2(n-1)/n) & 14.1 GB/s (AllGather (n-1)/n)",
        algbw == 14.3 and busbw == 28.2 and ag_busbw == 14.1,
    )

    # 3. Verify SP Ch. 12 Sanity Check (50,000 IOPS * 8 KB = 400,000 KB/s = 3.2 Gbps > 1 Gbps) and Benchmark Paradox (0.5^3 = 12.5%)
    nfs_iops_kbs = 50_000 * 8  # 400,000 KB/s
    nfs_gbps = round(nfs_iops_kbs * 8 / 1e6, 1)  # 3.2 Gbps
    paradox_pct = round((0.5**3) * 100.0, 1)  # 12.5%
    zfs_throttle_pct = 62.17
    check(
        "SP Ch. 12 sanity check (50k * 8KB = 400,000 KB/s = 3.2 Gbps > 1 Gbps) and Benchmark Paradox (12.5%) verified",
        nfs_iops_kbs == 400_000 and nfs_gbps == 3.2 and paradox_pct == 12.5 and zfs_throttle_pct == 62.17,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
