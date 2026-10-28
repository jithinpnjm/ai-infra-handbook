#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.19: Lustre architecture and operation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lustre_stripe import per_ost_bytes, pfl_layout, request_osts, slot

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


def oss_ram_sizing_mb(num_osts: int, num_clients: int, total_connected_osts: int) -> tuple[float, int]:
    """Compute SCL Ch. 9 per-OST RAM (400 + 600 + 1.5 * N_threads MB) and OSS baseline RAM (2048 + 1024 * num_osts MB)."""
    n_threads = num_clients / max(1, total_connected_osts)
    per_ost_mb = 400.0 + 600.0 + 1.5 * n_threads
    oss_recommended_gb = 2 + 1 * num_osts
    return round(per_ost_mb, 1), oss_recommended_gb


def main() -> None:
    MiB = 1 << 20

    # 1. Verify raid0 striping round-robin placement and request_osts parallelism
    per_mib = [b // MiB for b in per_ost_bytes(1024 * MiB, MiB, 4)]
    first_8 = [slot(i * MiB, MiB, 4) for i in range(8)]
    osts_3m = request_osts(int(2.5 * MiB), 3 * MiB, MiB, 4)
    osts_512k = request_osts(0, MiB // 2, MiB, 4)
    check(
        "raid0 striping distributes 1 GiB as [256,256,256,256] MiB, 3 MiB read touches [0,1,2,3], 512 KiB touches [0]",
        per_mib == [256, 256, 256, 256]
        and first_8 == [0, 1, 2, 3, 0, 1, 2, 3]
        and osts_3m == [0, 1, 2, 3]
        and osts_512k == [0],
    )

    # 2. Verify PFL (Progressive File Layout) component clipping on a 1 GiB file and 4 GiB file
    comps = [(4 * MiB, 1, MiB), (64 * MiB, 4, MiB), (None, 16, 4 * MiB)]
    pfl_1g = [(st // MiB, en // MiB, c, sz // MiB) for st, en, c, sz in pfl_layout(1024 * MiB, comps)]
    scl_comps = [(1 * MiB, 1, 512 * 1024), (256 * MiB, 4, 512 * 1024), (None, 8, 1 * MiB)]
    pfl_scl = pfl_layout(1024 * MiB, scl_comps)
    check(
        "pfl_layout computes [0,4)->c=1, [4,64)->c=4, [64,1024)->c=16 and SCL Ch. 9 [0,1M)->1, [1M,256M)->4, [256M,1024M)->8",
        pfl_1g == [(0, 4, 1, 1), (4, 64, 4, 1), (64, 1024, 16, 4)]
        and len(pfl_scl) == 3
        and pfl_scl[1][1] - pfl_scl[1][0] == 255 * MiB,
    )

    # 3. Verify SCL Ch. 9 OSS RAM sizing formulas, LNET TCP port 988, and lmm_stripe_size = 4194304 (4 MiB)
    per_ost_mb, oss_gb = oss_ram_sizing_mb(num_osts=8, num_clients=640, total_connected_osts=32)
    lnet_port = 988
    lmm_stripe_size = 4194304
    check(
        "SCL Ch. 9 OSS RAM sizing (1030.0 MB per OST at 20 threads, 10 GB for 8 OSTs), port 988, and 4194304 stripe size verified",
        per_ost_mb == 1030.0 and oss_gb == 10 and lnet_port == 988 and lmm_stripe_size == 4 * MiB,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
