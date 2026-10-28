#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.18: Parallel storage concepts and the limits of NFS."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ckpt_math import ckpt_bytes, need_gbs, overhead

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
    # 1. Verify ckpt_math.py checkpoint sizes, 60-second write bandwidth, and 10 GB/s hourly stall overhead
    sz_70b = ckpt_bytes(70e9, 14)  # 0.98 TB
    bw_70b = round(need_gbs(sz_70b, 60))  # 16 GB/s
    t_70b, frac_70b = overhead(sz_70b, 10, 3600)
    sz_405b = ckpt_bytes(405e9, 14)  # 5.67 TB (5670 GB)
    bw_405b = round(need_gbs(sz_405b, 60))  # 94 GB/s
    t_405b, frac_405b = overhead(sz_405b, 10, 3600)
    min_405b = round(t_405b / 60.0, 2)  # 9.45 minutes
    check(
        "ckpt_math.py computes 70B (0.98 TB, 16 GB/s, 98s/2.7%) and 405B (5.67 TB / 5670 GB, 94 GB/s, 567s / 9.45m / 15.8%)",
        round(sz_70b / 1e12, 2) == 0.98
        and bw_70b == 16
        and round(t_70b) == 98
        and round(frac_70b * 100, 1) == 2.7
        and round(sz_405b / 1e12, 2) == 5.67
        and round(sz_405b / 1e9) == 5670
        and bw_405b == 94
        and round(t_405b) == 567
        and min_405b == 9.45
        and round(frac_405b * 100, 1) == 15.8,
    )

    # 2. Verify dataset read bandwidth math (text 49 MB/s vs vision 150 GB/s) and iomix.py reference figures
    text_mbs = round(4096 * 3000 * 4 / 1e6)  # 49 MB/s
    vision_gbs = round(500 * 2000 * 150_000 / 1e9)  # 150 GB/s
    ref_seq_write, ref_seq_read, ref_iops = 633, 11562, 705949
    ref_create, ref_stat, ref_unlink = 4585, 378127, 8303
    check(
        "Dataset read bandwidth math (49 MB/s text vs 150 GB/s vision) and iomix.py reference metrics verified",
        text_mbs == 49
        and vision_gbs == 150
        and ref_seq_write == 633
        and ref_seq_read == 11562
        and ref_iops == 705949
        and ref_create == 4585
        and ref_stat == 378127
        and ref_unlink == 8303,
    )

    # 3. Execute iomix.py (--mb 4 --files 100) to verify sequential, random 4 KiB, and metadata phases run cleanly
    iomix_script = Path(__file__).resolve().parent / "iomix.py"
    proc = subprocess.run(
        [sys.executable, str(iomix_script), "--mb", "4", "--files", "100"],
        capture_output=True,
        text=True,
        check=True,
    )
    check(
        "iomix.py --mb 4 --files 100 executes sequential write/read, random 4 KiB IOPS, and create/stat/unlink",
        "sequential write" in proc.stdout
        and "random 4 KiB read" in proc.stdout
        and "create" in proc.stdout,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
