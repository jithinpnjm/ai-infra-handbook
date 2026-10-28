#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.14: Overlay versus routed pod networking: VXLAN, BGP with Calico, eBPF with Cilium."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overlay_bgp_cilium_planner import (
    compare_policy_scaling_ip_vs_identity,
    compute_bgp_session_counts,
    select_calico_cross_subnet_mode,
    select_primary_cni_node_interface,
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
    # 1. Section 3: BGP session scaling at 500 nodes (Full-Mesh 124,750 vs Route Reflectors 1,494 vs ToR eBGP 1,000)
    bgp = compute_bgp_session_counts(node_count=500, route_reflector_count=3, tor_uplinks_per_node=2)
    same_rack = select_calico_cross_subnet_mode("10.0.1.11", "10.0.1.12", "10.0.1.0/24", "vxlan")
    cross_rack = select_calico_cross_subnet_mode("10.0.1.11", "10.0.2.15", "10.0.1.0/24", "vxlan")
    check(
        "500-node full-mesh requires 124,750 BGP sessions vs 1,000 ToR eBGP sessions, and CrossSubnet routes intra-rack natively",
        bgp["full_mesh_total_sessions"] == 124_750
        and bgp["tor_ebgp_total_sessions"] == 1_000
        and same_rack == "native_routed"
        and cross_rack == "encapsulated_vxlan",
    )

    # 2. Section 4: Cilium numeric Security Identity scaling vs IP-pair rule explosion
    scale = compare_policy_scaling_ip_vs_identity(
        source_pods=1000,
        dest_pods=500,
        unique_source_label_sets=2,
        unique_dest_label_sets=1,
    )
    check(
        "Cilium Security Identities compress 500,000 IP-pair combinations (1000x500 pods) into 2 BPF policy map entries",
        scale["ip_pair_combinations"] == 500_000 and scale["cilium_identity_map_entries"] == 2,
    )

    # 3. Section 6: Multi-homed GPU node CNI interface selection (excluding RDMA ens1f* / ib* interfaces)
    ifaces = [
        {"name": "ib0", "ip": "172.16.0.11"},
        {"name": "ens1f0np0", "ip": "192.168.10.11"},
        {"name": "eth0", "ip": "10.0.1.11"},
    ]
    chosen = select_primary_cni_node_interface(ifaces)
    check(
        "select_primary_cni_node_interface skips ib0 and ens1f0np0 RDMA rails and selects management eth0",
        chosen == "eth0",
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
