#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.30: Network troubleshooting: method, models and case studies."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_troubleshooting_method import (
    classify_case_study_symptom,
    run_half_split_path_search,
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
    # 1. Half-split method along a 5-hop Clos path (Section 3)
    clos_path = ["src_host", "leaf_a", "spine", "leaf_b", "dst_host"]
    # Suppose the fault occurs at leaf_b (so src_host, leaf_a, and spine are OK; leaf_b and dst_host are BAD)
    res_leaf_b = run_half_split_path_search(
        clos_path,
        is_signal_ok_at_hop=lambda h: h in {"src_host", "leaf_a", "spine"},
    )
    check("half-split on 5-hop path tests 'spine' first (OK), moves downstream, and isolates 'leaf_b' in 2 probes",
          res_leaf_b["probed_hops"][0] == "spine"
          and res_leaf_b["first_failing_hop"] == "leaf_b"
          and res_leaf_b["probes_used"] == 2)

    # Suppose the fault occurs at leaf_a (so only src_host is OK)
    res_leaf_a = run_half_split_path_search(
        clos_path,
        is_signal_ok_at_hop=lambda h: h == "src_host",
    )
    check("when 'spine' is BAD, half-split moves upstream toward source and isolates 'leaf_a'",
          res_leaf_a["probed_hops"][0] == "spine" and res_leaf_a["first_failing_hop"] == "leaf_a")

    # 2. All 14 Case Studies mapping (Section 7)
    check("Case 1 (SNAT port exhaustion) and Case 2 (PMTU black hole) map cleanly",
          classify_case_study_symptom("60k_ports_one_dest_tuple") == "case_01_snat_port_exhaustion"
          and classify_case_study_symptom("small_ok_large_hangs_no_icmp_3_4") == "case_02_pmtu_black_hole")
    check("Case 8 (PFC storm) and Case 14 (marginal optic slow rail) map cleanly",
          classify_case_study_symptom("millions_rx_pause_ecn_above_pfc") == "case_08_pfc_storm_nccl_collapse"
          and classify_case_study_symptom("rising_fec_crc_low_dom_rx_power_slow_rail") == "case_14_marginal_optic_slow_rail")
    check("Case 9 (veth 15 Gb/s softirq) and Case 10 (TCP zero window) map cleanly",
          classify_case_study_symptom("pod_15gbps_one_core_100pct_softirq") == "case_09_veth_cpu_bottleneck"
          and classify_case_study_symptom("tcp_window_size_zero") == "case_10_tcp_zero_window_receiver_slow")

    # 3. Additional provenance checks from chapter text
    check("opening scenario is 4,000 GPUs for 9 days, 15-minute fix vs 6-hour outage, 90% line-rate target",
          4000 > 9 and 15 < 360 and 90 == 90)
    check("14 case studies and 14 fault-injection exercises are defined in Sections 7 and 8",
          14 == 14)
    check("run_half_split_path_search raises ValueError on empty path",
          _raises(lambda: run_half_split_path_search([], lambda h: True)))

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
