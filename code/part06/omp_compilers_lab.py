#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.5: OpenMP, compilers and optimisation flags."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from omp_compilers import (
    check_hybrid_oversubscription,
    flexlm_quorum_and_seat_availability,
    fp_relative_error_pct,
    triad_bandwidth_gbps,
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
    # 1. Section 2: STREAM triad memory bandwidth calculation (3 * 50M * 8 bytes / elapsed_s)
    bw1 = triad_bandwidth_gbps(50_000_000, 8, 18.1)
    bw8 = triad_bandwidth_gbps(50_000_000, 8, 14.1)
    check(
        "triad_bandwidth_gbps matches omp_scaling.c (66.3 GB/s at 18.1 ms on 1 thread, 85.1 GB/s at 14.1 ms on 8 threads)",
        bw1 == 66.3 and 85.0 <= bw8 <= 85.5,
    )

    # 2. Section 3 & 6: Hybrid MPI+OpenMP oversubscription check and strict vs -ffast-math FP32 reduction accuracy
    over = check_hybrid_oversubscription(mpi_ranks_per_node=8, omp_threads_per_rank=64, physical_cores_per_node=64)
    good = check_hybrid_oversubscription(mpi_ranks_per_node=8, omp_threads_per_rank=8, physical_cores_per_node=64)
    strict_err = fp_relative_error_pct(2293365.0, 2446257.2)
    fast_err = fp_relative_error_pct(2445485.5, 2446257.2)
    check(
        "check_hybrid_oversubscription catches 8x64=512 thread oversubscription (8.0x) and fp_relative_error_pct shows 6.25% vs 0.03% error",
        over["oversubscribed"] is True
        and over["oversubscription_ratio"] == 8.0
        and good["oversubscribed"] is False
        and 6.20 <= strict_err <= 6.30
        and fast_err == 0.03,
    )

    # 3. Section 5: SCL Chapter 21 FlexLM >=50% server quorum and 15-minute floating seat lease hold
    q_ok = flexlm_quorum_and_seat_availability(total_servers=3, online_servers=2, total_seats=3, recent_calls_within_15m=2)
    q_lost = flexlm_quorum_and_seat_availability(total_servers=3, online_servers=1, total_seats=3, recent_calls_within_15m=0)
    check(
        "flexlm_quorum_and_seat_availability enforces >=50% server quorum (2/3 online -> 1 free seat; 1/3 online -> 0 seats) and 15m lease",
        q_ok["has_quorum"] is True
        and q_ok["free_seats"] == 1
        and q_ok["lease_hold_minutes"] == 15
        and q_lost["has_quorum"] is False
        and q_lost["free_seats"] == 0,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
