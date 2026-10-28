#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.3: Parallel computing concepts: Amdahl, scaling, shared memory versus message passing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scaling import (
    amdahl,
    gustafson,
    hockney_message_time_us,
    karp_flatt,
    ring_allreduce_volume_per_rank,
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
    # 1. Section 2 & 3: Amdahl's Law (strong scaling) vs Gustafson's Law (weak scaling)
    check(
        "amdahl(0.99, 1024) == 91.2x (9% efficiency, limit 100x) and gustafson(0.99, 1024) == 1013.77x",
        round(amdahl(0.99, 1024), 1) == 91.2
        and round(amdahl(0.999, 1024), 1) == 506.2
        and round(gustafson(0.99, 1024), 2) == 1013.77,
    )

    # 2. Section 4 & 5: Karp-Flatt serial fraction e = (1/S - 1/n) / (1 - 1/n) rising on 2, 4, 8 workers
    e2 = round(karp_flatt(1.85, 2), 3)
    e4 = round(karp_flatt(2.84, 4), 3)
    e8 = round(karp_flatt(3.37, 8), 3)
    check(
        "karp_flatt rises from 0.081/0.083 (n=2) -> 0.136 (n=4) -> 0.196 (n=8), proving growing parallel/imbalance overhead",
        0.080 <= e2 <= 0.085 and 0.134 <= e4 <= 0.137 and 0.195 <= e8 <= 0.197 and (e2 < e4 < e8),
    )

    # 3. Section 8: Hockney communication cost model T(m) = alpha + m/beta and Ring AllReduce 2*(n-1)/n volume
    ib_msg = hockney_message_time_us(message_bytes=100_000, alpha_us=2.0, beta_gbps=50.0)
    vol_8 = ring_allreduce_volume_per_rank(tensor_bytes=1_000_000_000, num_ranks=8)
    check(
        "hockney_message_time_us crossover (alpha*beta = 100,000 B at 2 us & 50 GB/s) and ring_allreduce_volume_per_rank (1.75 GB for 1 GB across 8 ranks)",
        ib_msg["crossover_bytes"] == 100_000.0
        and ib_msg["total_us"] == 4.0
        and ib_msg["latency_share"] == 0.5
        and abs(vol_8 - 1_750_000_000.0) < 1e-3,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
