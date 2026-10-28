#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.21: Parallel I/O and checkpoint patterns."""
import math
import subprocess
import sys
from pathlib import Path

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


def young_daly_interval_min(ckpt_cost_min: float, mtbf_hours: float) -> int:
    """Compute Young/Daly optimal checkpoint interval T_opt = round(sqrt(2 * C * MTBF))."""
    return round(math.sqrt(2.0 * ckpt_cost_min * (mtbf_hours * 60.0)))


def main() -> None:
    # 1. Execute ckpt_atomic.py and verify all 5 crash-recovery and SHA-256 corruption assertions
    script = Path(__file__).resolve().parent / "ckpt_atomic.py"
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=True)
    out = proc.stdout
    check(
        "ckpt_atomic.py survives before_rename & before_latest crashes and falls back to step-300 on shard-2 bit rot",
        "step 100: committed                latest pointer=step-100  newest_valid=step-100" in out
        and "step 200: CRASH (before_rename)    latest pointer=step-100  newest_valid=step-100" in out
        and "step 300: CRASH (before_latest)    latest pointer=step-100  newest_valid=step-300" in out
        and "step 400: committed                latest pointer=step-400  newest_valid=step-400" in out
        and "after corrupting step-400/shard-2: newest_valid=step-300" in out,
    )

    # 2. Verify Young/Daly optimal checkpoint interval (C=1 min, MTBF=6 h -> 27 min)
    t_opt = young_daly_interval_min(1.0, 6.0)
    check(
        "Young/Daly formula sqrt(2 * 1 min * 360 min) rounds to 27 minutes",
        t_opt == 27,
    )

    # 3. Verify ASP Ch. 5 GPU storage throughput scaling (8 GPUs -> 1.6 GB/s, 72 GPUs -> 14.4 GB/s) & gdsio (+20%)
    node_8gpu_gbs = round(8 * 200 / 1000.0, 1)  # 1.6 GB/s
    rack_72gpu_gbs = round(72 * 200 / 1000.0, 1)  # 14.4 GB/s (within 14-20 GB/s NVL72 budget)
    gds_gain_pct = round((9.6 - 8.0) / 8.0 * 100.0, 1)  # +20.0%
    io_wait_speedup = 30 // 5  # 6x reduction in I/O wait fraction
    check(
        "ASP Ch. 5 storage math: 8 GPUs=1.6 GB/s, 72 GPUs=14.4 GB/s, gdsio 8.0->9.6 GB/s (+20%), I/O wait 30%->5% (6x)",
        node_8gpu_gbs == 1.6 and 14.0 <= rack_72gpu_gbs <= 20.0 and gds_gain_pct == 20.0 and io_wait_speedup == 6,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
