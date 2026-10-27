#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.17: Memory management: virtual memory, NUMA, huge pages, OOM."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from memory_numa_oom import (
    audit_training_node_ram_budget,
    compute_oom_effective_score,
    compute_process_memory_accounting,
    compute_tlb_reach_bytes,
    compute_zone_watermarks_kib,
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
    # 1. TLB reach: 4 KiB pages vs 2 MiB and 1 GiB huge pages (Sections 2 & 8)
    r_4k = compute_tlb_reach_bytes(num_entries=64, page_size_bytes=4096)
    check("64-entry TLB with 4 KiB pages has reach = 262,144 bytes (0.25 MiB)",
          r_4k["reach_bytes"] == 262144 and r_4k["reach_mib"] == 0.25)
    r_2m = compute_tlb_reach_bytes(num_entries=64, page_size_bytes=2 * (1 << 20))
    check("64-entry TLB with 2 MiB huge pages has reach = 128 MiB (512x larger than 4 KiB)",
          r_2m["reach_mib"] == 128.0 and r_2m["reach_bytes"] == 512 * r_4k["reach_bytes"])
    r_1g = compute_tlb_reach_bytes(num_entries=64, page_size_bytes=1 << 30)
    check("64-entry TLB with 1 GiB huge pages has reach = 65,536 MiB (64 GiB)",
          r_1g["reach_mib"] == 65536.0)

    # 2. USS, PSS, and RSS shared memory accounting (Section 2)
    m4 = compute_process_memory_accounting(private_kib=100000, shared_kib=400000, num_sharing_processes=4)
    check("process with 100 MiB private and 400 MiB shared across 4 workers has USS=100m, PSS=200m, RSS=500m",
          m4 == {"uss_kib": 100000, "pss_kib": 200000, "rss_kib": 500000})
    check("summing PSS across all 4 workers (4 * 200,000 = 800,000 KiB) equals true physical RAM (4*100k + 400k)",
          4 * m4["pss_kib"] == 4 * 100000 + 400000 and 4 * m4["rss_kib"] == 2000000)

    # 3. Zone watermarks (min, low, high) from min_free_kbytes & watermark_scale_factor (Section 4)
    wm_def = compute_zone_watermarks_kib(total_ram_kib=100000000, min_free_kib=90000, watermark_scale_factor=10)
    check("100 GB RAM with watermark_scale_factor=10 (0.1%) has step=100,000 KiB, low=190,000 KiB, high=290,000 KiB",
          wm_def["step_kib"] == 100000 and wm_def["low_kib"] == 190000 and wm_def["high_kib"] == 290000)
    wm_tuned = compute_zone_watermarks_kib(total_ram_kib=100000000, min_free_kib=90000, watermark_scale_factor=100)
    check("raising watermark_scale_factor to 100 (1.0%) widens step to 1,000,000 KiB so kswapd wakes much earlier",
          wm_tuned["step_kib"] == 1000000 and wm_tuned["low_kib"] > wm_def["low_kib"])

    # 4. OOM badness score and oom_score_adj (Section 5)
    check("oom_score_adj=-1000 makes sshd immune (score 0) regardless of RSS",
          compute_oom_effective_score(500000, 1000000, oom_score_adj=-1000) == 0)
    check("process using 40% of RAM with oom_score_adj=0 has oom_score=400",
          compute_oom_effective_score(400000, 1000000, oom_score_adj=0) == 400)
    check("batch worker using 40% of RAM with oom_score_adj=+500 has oom_score=900",
          compute_oom_effective_score(400000, 1000000, oom_score_adj=500) == 900)

    # 5. Training node host RAM budget (Section 11)
    b_ok = audit_training_node_ram_budget(
        total_ram_gib=512.0, num_gpus=8, workers_per_gpu=8, gb_per_worker=2.0, pinned_buffers_gib=32.0, os_and_daemons_gib=16.0
    )
    check("8 GPUs x 8 workers x 2 GiB (128 GiB) + 32 GiB pinned + 16 GiB OS = 176 GiB fits in 512 GiB with 336 GiB for cache",
          b_ok["workers_total_gib"] == 128.0 and b_ok["required_gib"] == 176.0 and b_ok["fits_in_ram"] is True)
    b_oom = audit_training_node_ram_budget(
        total_ram_gib=256.0, num_gpus=8, workers_per_gpu=16, gb_per_worker=2.0, pinned_buffers_gib=32.0, os_and_daemons_gib=16.0
    )
    check("8 GPUs x 16 workers x 2 GiB (256 GiB) + 48 GiB overhead = 304 GiB exceeds 256 GiB RAM (fits_in_ram=False)",
          b_oom["workers_total_gib"] == 256.0 and b_oom["fits_in_ram"] is False)

    # 6. Additional checks from chapter text
    check("256 GiB dataset with 4 KiB pages requires 67,108,864 (~67 million) PTEs",
          (256 * (1 << 30)) // 4096 == 67108864)
    check("DDR5-4800 per-channel bandwidth is 38.4 GB/s (4800 MT/s * 8 bytes)",
          4800 * 8 / 1000.0 == 38.4)
    check("OOM SIGKILL exit status 137 equals 128 + 9", 128 + 9 == 137)
    check("buddy allocator order 9 is 2^9 * 4 KiB = 2 MiB", (1 << 9) * 4096 == 2 * (1 << 20))
    check("CPython pymalloc arena size is 256 KiB and glibc mmap threshold is 128 KiB",
          256 * 1024 == 262144 and 128 * 1024 == 131072)
    check("default vm.max_map_count is 65530 and GPU node tuned value is 1048576",
          65530 < 262144 < 1048576)
    check("compute_tlb_reach_bytes raises ValueError on zero entries",
          _raises(lambda: compute_tlb_reach_bytes(0, 4096)))
    check("compute_oom_effective_score raises ValueError on out-of-range oom_score_adj",
          _raises(lambda: compute_oom_effective_score(100, 1000, -1500)))
    check("audit_training_node_ram_budget raises ValueError on zero RAM",
          _raises(lambda: audit_training_node_ram_budget(0.0, 8, 4, 2.0, 16.0)))

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
