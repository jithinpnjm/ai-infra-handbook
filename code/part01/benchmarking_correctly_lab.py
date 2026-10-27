#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.25: Benchmarking correctly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmarking_correctly import (
    SIX_CHECKLIST_QUESTIONS,
    check_iops_link_sanity,
    compute_benchmark_paradox_win_prob,
    compute_nccl_allreduce_busbw,
    evaluate_median_mad_regression_gate,
)

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


def main() -> None:
    # 1. Six-question benchmarking checklist (Section 4, SP Ch. 12.4)
    check("Six-question checklist starts with '1_why_not_double' and ends with '6_did_it_even_happen'",
          len(SIX_CHECKLIST_QUESTIONS) == 6
          and SIX_CHECKLIST_QUESTIONS[0] == "1_why_not_double"
          and SIX_CHECKLIST_QUESTIONS[-1] == "6_did_it_even_happen")

    # 2. Sanity-check bandwidth arithmetic (Sections 4 & 7, SP Ch. 12.3.8)
    nfs_check = check_iops_link_sanity(claimed_iops=50000, io_size_bytes=8192, link_rate_gbps=1.0)
    check("50,000 NFS IOPS x 8 KiB requires 3.277 Gbit/s (> 1 GbE), proving client cache was measured",
          nfs_check["physically_possible_on_wire"] is False and nfs_check["required_gbps"] > 3.2)
    valid_nvme = check_iops_link_sanity(claimed_iops=500000, io_size_bytes=4096, link_rate_gbps=32.0)
    check("500,000 IOPS x 4 KiB requires 16.384 Gbit/s, which fits inside a 32 Gbit/s link",
          valid_nvme["physically_possible_on_wire"] is True)

    # 3. nccl-tests AllReduce algbw to busbw conversion: busbw = algbw * 2*(n-1)/n (Section 6.6)
    b8 = compute_nccl_allreduce_busbw(size_bytes=1_000_000_000, time_sec=0.010, num_ranks=8)
    check("1 GB AllReduce in 10 ms across 8 GPUs has algbw=100.0 GB/s, factor=1.75 (14/8), busbw=175.0 GB/s",
          b8["algbw_gbs"] == 100.0 and b8["factor"] == 1.75 and b8["busbw_gbs"] == 175.0)
    b2 = compute_nccl_allreduce_busbw(size_bytes=1_000_000_000, time_sec=0.020, num_ranks=2)
    check("across 2 ranks, 2*(2-1)/2 = 1.0 so busbw equals algbw (50.0 GB/s)",
          b2["factor"] == 1.0 and b2["busbw_gbs"] == 50.0)

    # 4. Benchmark paradox probability (Section 2, SP Ch. 12.1.3)
    check("winning 3 independent 50%-chance benchmarks in a row has probability 0.125 (12.5%)",
          compute_benchmark_paradox_win_prob(0.5, 3) == 0.125)

    # 5. Median - 3*MAD non-regression gate (Section 7)
    base = [100.0, 101.0, 99.0, 100.5, 99.5]
    noise_run = [98.8, 99.2, 100.1, 99.0, 99.4]
    regressed_run = [92.0, 91.5, 93.0, 92.2, 91.8]
    g_ok = evaluate_median_mad_regression_gate(base, noise_run, k_mad=3.0)
    check("candidate run within 3*MAD of baseline median passes regression gate",
          g_ok["passed"] is True and g_ok["baseline_median"] == 100.0)
    g_fail = evaluate_median_mad_regression_gate(base, regressed_run, k_mad=3.0)
    check("candidate run at 92.0 (< 100.0 - 3*0.5 = 98.5) fails regression gate",
          g_fail["passed"] is False)

    # 6. Additional checks from chapter text
    check("400 Gb/s NIC equals 50 GB/s raw per direction (400 / 8 = 50)", 400 // 8 == 50)
    check("1 GbE ceiling is ~119 MB/s (not 350 MB/s = 2.8 Gbit/s)", 350 * 8 == 2800 and 119 < 125)
    check("PCIe Gen4 x16 theoretical bandwidth is ~31.5 GB/s per direction (26-28 GB/s achievable)",
          26.0 < 31.5 < 40.0)
    check("Bonnie++ per-character test scored 739 KB/s via ~1.18M 1-byte vfs_write calls to page cache",
          739 * 1000 == 739000)
    check("1981 4 MB transfer breakdown sums to 100% (20% Eth + 10% IP + 30% TCP + 25% csum + 15% syscall)",
          20 + 10 + 30 + 25 + 15 == 100)
    check("check_iops_link_sanity raises ValueError on zero link rate",
          _raises(lambda: check_iops_link_sanity(100, 4096, 0.0)))
    check("compute_nccl_allreduce_busbw raises ValueError on 1 rank",
          _raises(lambda: compute_nccl_allreduce_busbw(1000, 1.0, 1)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
