#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.18: Data-center topologies: Clos, leaf-spine, oversubscription, failure domains and resilience."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dc_topologies_clos import (
    compute_5stage_max_endpoints_1to1,
    compute_availability_and_downtime,
    compute_oversubscription_and_spine_loss,
    compute_torus_diameter,
    size_clos3_fabric,
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
    # 1. 3-stage and 5-stage Clos non-blocking endpoint scaling (Section 3 & 11)
    c64 = size_clos3_fabric(radix=64)
    check("64-port 3-stage 1:1 Clos has 64 leaves, 32 spines (96 switches), and R^2/2 = 2,048 endpoints",
          c64["leaves"] == 64
          and c64["spines"] == 32
          and c64["total_switches"] == 96
          and c64["max_endpoints"] == 2048
          and c64["leaf_spine_cables"] == 2048)

    c32 = size_clos3_fabric(radix=32)
    check("32-port 3-stage 1:1 Clos supports 32^2 / 2 = 512 endpoints",
          c32["max_endpoints"] == 512)

    check("64-port 5-stage 1:1 Clos supports R^3 / 4 = 65,536 endpoints",
          compute_5stage_max_endpoints_1to1(64) == 65536)

    # 2. Oversubscription ratio and single-spine failure capacity (Section 3 & 11)
    ov_32 = compute_oversubscription_and_spine_loss(12800.0, 12800.0, num_spines=32)
    check("1:1 leaf with 32 spines retains 96.9% capacity (3.1% loss <= 5% target) when 1 spine fails",
          ov_32["oversubscription_ratio"] == 1.0
          and ov_32["surviving_capacity_pct"] == 96.9
          and ov_32["capacity_loss_pct"] == 3.1)

    ov_ex = compute_oversubscription_and_spine_loss(320.0, 180.0, num_spines=4)
    check("320 Gb/s down vs 180 Gb/s up has 1.78:1 oversubscription, and 4 spines retain 75.0% on 1 spine loss",
          ov_ex["oversubscription_ratio"] == 1.78 and ov_ex["surviving_capacity_pct"] == 75.0)

    # 3. Multidimensional torus diameter sum(n_i // 2) (Section 6)
    check("4x4x4 3D torus has diameter 2 + 2 + 2 = 6 hops",
          compute_torus_diameter([4, 4, 4]) == 6)
    check("8x8 2D torus has diameter 4 + 4 = 8 hops",
          compute_torus_diameter([8, 8]) == 8)

    # 4. MTBF / MTTR availability and 'nines' downtime per year (Section 10)
    a_4nines = compute_availability_and_downtime(mtbf_hours=9999.0, mttr_hours=1.0)
    check("MTBF=9999h, MTTR=1h gives 99.99% availability ('four nines') = 52.6 min/year downtime",
          a_4nines["availability_pct"] == 99.99 and a_4nines["downtime_min_per_year"] == 52.6)

    a_5nines = compute_availability_and_downtime(mtbf_hours=99999.0, mttr_hours=1.0)
    check("99.999% availability ('five nines') = 5.3 min/year downtime",
          a_5nines["availability_pct"] == 99.999 and a_5nines["downtime_min_per_year"] == 5.3)

    # 5. Additional provenance checks from Section 11 4,096-GPU worked design
    check("Section 11 4,096-GPU 5-stage design uses 128 leaves + 128 spines + 32 super-spines = 288 switches",
          128 + 128 + 32 == 288)
    check("Section 11 cables: 4,096 server + 4,096 leaf-spine + 2,048 spine-superspine (2:1)",
          4096 // 2048 == 2)
    check("scheduled fabric cell size range is 64 to 256 bytes", 64 < 256)
    check("size_clos3_fabric raises ValueError on odd radix",
          _raises(lambda: size_clos3_fabric(63)))
    check("compute_torus_diameter raises ValueError on empty dimensions",
          _raises(lambda: compute_torus_diameter([])))

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
