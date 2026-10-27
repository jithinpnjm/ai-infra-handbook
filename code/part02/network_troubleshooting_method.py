"""Chapter 2.30 model: Half-split (binary search) signal-path fault isolator,
connectivity decision-tree classifier, and 14-case-study symptom-to-root-cause
diagnostic matcher.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 24 ("Troubleshooting": purpose, components, how/what/accurate models,
  shifting between models, half-split and move, manipulation, simplify before
  testing, immediate vs permanent fix and technical debt).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapters 2 and 10 (USE method, tools method, workload characterization,
  latency and TCP analysis).
- nvidia-devops/volume-01/03-linux-networking-masterclass.md (14 production
  networking case studies).
"""
from typing import Callable, Dict, List


def run_half_split_path_search(
    hops: List[str],
    is_signal_ok_at_hop: Callable[[str], bool],
) -> Dict[str, object]:
    """Use the half-split (binary search) method to find the first failing hop along hops."""
    if not hops:
        raise ValueError("hops list must be non-empty")
    probed: List[str] = []
    lo = 0
    hi = len(hops) - 1
    first_bad_idx = None

    while lo <= hi:
        mid = (lo + hi) // 2
        hop = hops[mid]
        probed.append(hop)
        if is_signal_ok_at_hop(hop):
            # Signal is still good at mid -> fault is further downstream (toward destination)
            lo = mid + 1
        else:
            # Signal is already broken at mid -> record and move upstream (toward source)
            first_bad_idx = mid
            hi = mid - 1

    return {
        "first_failing_hop": None if first_bad_idx is None else hops[first_bad_idx],
        "probed_hops": probed,
        "probes_used": len(probed),
    }


def classify_case_study_symptom(evidence: str) -> str:
    """Map key diagnostic evidence to the corresponding Section 7 Case Study (1..14)."""
    mapping = {
        "60k_ports_one_dest_tuple": "case_01_snat_port_exhaustion",
        "small_ok_large_hangs_no_icmp_3_4": "case_02_pmtu_black_hole",
        "nf_conntrack_table_full": "case_03_conntrack_table_full",
        "multi_nic_same_subnet_arp_flux": "case_04_arp_flux_and_rp_filter",
        "udp_rcvbuf_errors_rising": "case_05_udp_receive_buffer_overflow",
        "exact_5min_outage_flapping_optic": "case_06_bgp_route_dampening",
        "receiver_sees_bad_tcp_checksum": "case_07_tx_checksum_offload_bug",
        "millions_rx_pause_ecn_above_pfc": "case_08_pfc_storm_nccl_collapse",
        "pod_15gbps_one_core_100pct_softirq": "case_09_veth_cpu_bottleneck",
        "tcp_window_size_zero": "case_10_tcp_zero_window_receiver_slow",
        "host_bgp_unequal_paths_reordering": "case_11_asymmetric_ecmp_reordering",
        "multicast_fails_in_vxlan_overlay": "case_12_overlay_multicast_blackhole",
        "parallel_a_aaaa_udp_5s_timeout": "case_13_k8s_dns_conntrack_race",
        "rising_fec_crc_low_dom_rx_power_slow_rail": "case_14_marginal_optic_slow_rail",
    }
    if evidence not in mapping:
        raise ValueError(f"Unknown evidence key: {evidence}")
    return mapping[evidence]
