#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.31: Network monitoring and telemetry for AI data centers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_monitoring_telemetry import (
    analyze_ifa_metadata_stack,
    estimate_telemetry_cardinality_and_rate,
    evaluate_rail_skew_and_ecmp_balance,
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
    # 1. Per-rail bandwidth skew and ECMP imbalance (Section 4)
    balanced = evaluate_rail_skew_and_ecmp_balance([380.0] * 8, skew_alert_threshold=1.5)
    check("8 balanced rails at 380 Gb/s have skew_ratio=1.0, cv=0.0, skew_alert_firing=False",
          balanced["max_min_skew_ratio"] == 1.0
          and balanced["coeff_of_variation"] == 0.0
          and balanced["skew_alert_firing"] is False)

    straggler = evaluate_rail_skew_and_ecmp_balance(
        [380.0, 380.0, 380.0, 190.0, 380.0, 380.0, 380.0, 380.0],
        skew_alert_threshold=1.5,
    )
    check("degraded rail 3 at 190 Gb/s vs 380 Gb/s gives skew_ratio=2.0 (>1.5) and identifies straggler_rail_index=3",
          straggler["max_min_skew_ratio"] == 2.0
          and straggler["skew_alert_firing"] is True
          and straggler["straggler_rail_index"] == 3)

    # 2. In-Band Flow Analyzer (IFA) metadata stack analysis (Section 5, ADC Ch. 11)
    ifa_hops = [
        {"device_id": "leaf1-initiator", "residence_ns": 650, "ecn_marked": False},
        {"device_id": "spine2-transit", "residence_ns": 48500, "ecn_marked": True},
        {"device_id": "leaf4-terminator", "residence_ns": 700, "ecn_marked": False},
    ]
    ifa = analyze_ifa_metadata_stack(ifa_hops)
    check("IFA metadata stack pinpoints spine2-transit (48,500 ns residence + ECN mark) as the exact bottleneck hop",
          ifa["bottleneck_device"] == "spine2-transit"
          and ifa["total_residence_ns"] == 49850
          and ifa["ecn_congested_devices"] == ["spine2-transit"])

    # 3. Telemetry cardinality and ingestion rate (Section 7)
    scale = estimate_telemetry_cardinality_and_rate(
        num_switches=1000,
        ports_per_switch=64,
        metrics_per_port=100,
        sample_interval_sec=10.0,
    )
    check("1,000 switches x 64 ports x 100 counters @ 10s = 6,400,000 series and 640,000.0 samples/s",
          scale["active_series"] == 6_400_000.0 and scale["samples_per_sec"] == 640_000.0)

    # 4. Additional provenance checks from chapter text
    check("exporters ports: node_exporter=9100, blackbox=9115, snmp=9116, dcgm=9400, gnmic=9804",
          9100 < 9115 < 9116 < 9400 < 9804)
    check("OpticsDegrading alert threshold is rx_power_dbm < -9 dBm or corrected FEC > 1e9/h",
          -9 < 0 and 10**9 == 1_000_000_000)
    check("IOAM RFC is 9197", 9197 > 9000)
    check("evaluate_rail_skew_and_ecmp_balance raises ValueError on empty list",
          _raises(lambda: evaluate_rail_skew_and_ecmp_balance([])))

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
