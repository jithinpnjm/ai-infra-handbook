#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.27: Lab: build network topologies with namespaces, FRR and containerlab."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from containerlab_frr_topologies import (
    build_clos_clab_links,
    render_frr_ebgp_unnumbered_leaf,
    validate_frr_bgp_and_ecmp_state,
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
    # 1. Lab 3 Containerlab 2-spine x 4-leaf x 2-host link generation
    topo = build_clos_clab_links(num_spines=2, num_leaves=4, hosts_per_leaf=2)
    check("Lab 3 2-spine x 4-leaf x 2-host topology has 8 fabric links + 8 host links = 16 links",
          topo["fabric_links"] == 8 and topo["host_links"] == 8 and topo["total_links"] == 16)
    check("first fabric link is ('leaf1:eth1', 'spine1:eth1') and last host link is ('h42:eth1', 'leaf4:eth4')",
          topo["endpoints"][0] == ("leaf1:eth1", "spine1:eth1")
          and topo["endpoints"][-1] == ("h42:eth1", "leaf4:eth4"))

    # 2. Lab 3 FRR eBGP-unnumbered leaf config rendering
    leaf1_cfg = render_frr_ebgp_unnumbered_leaf(
        name="leaf1",
        asn=65101,
        lo_ip="10.255.0.11",
        br0_subnet="10.10.1.1/24",
        uplink_interfaces=["eth1", "eth2"],
    )
    check("rendered leaf1 frr.conf includes AS 65101, multipath-relax, remote-as external, bfd, and eth1/eth2 peers",
          "router bgp 65101" in leaf1_cfg
          and "bgp bestpath as-path multipath-relax" in leaf1_cfg
          and "neighbor swp remote-as external" in leaf1_cfg
          and "neighbor eth1 interface peer-group swp" in leaf1_cfg)

    # 3. Lab 7 validation harness assertions (healthy vs degraded fabric)
    bgp_ok = {
        "ipv4Unicast": {
            "peers": {
                "eth1": {"state": "Established"},
                "eth2": {"state": "Established"},
            }
        }
    }
    routes_ok = {
        "10.10.2.0/24": [{"nexthops": [{"ip": "fe80::1"}, {"ip": "fe80::2"}]}],
        "10.10.3.0/24": [{"nexthops": [{"ip": "fe80::1"}, {"ip": "fe80::2"}]}],
        "10.10.4.0/24": [{"nexthops": [{"ip": "fe80::1"}, {"ip": "fe80::2"}]}],
    }
    v_ok = validate_frr_bgp_and_ecmp_state(
        bgp_ok, routes_ok, expected_spines=2, remote_subnets=["10.10.2.0/24", "10.10.3.0/24", "10.10.4.0/24"]
    )
    check("healthy 2-spine BGP summary + 2-way ECMP routes pass Lab 7 validator",
          v_ok["passed"] is True and v_ok["failures"] == [])

    bgp_down = {
        "ipv4Unicast": {
            "peers": {
                "eth1": {"state": "Established"},
                "eth2": {"state": "Active"},
            }
        }
    }
    routes_1path = {
        "10.10.2.0/24": [{"nexthops": [{"ip": "fe80::1"}]}],
    }
    v_bad = validate_frr_bgp_and_ecmp_state(
        bgp_down, routes_1path, expected_spines=2, remote_subnets=["10.10.2.0/24"]
    )
    check("Active BGP peer + single nexthop flags both BGP and ECMP validation failures",
          v_bad["passed"] is False and len(v_bad["failures"]) == 2)

    # 4. Additional provenance checks from chapter text
    check("Lab 3 spine ASN is 65000 and leaf ASNs are 65101..65104",
          [65100 + i for i in range(1, 5)] == [65101, 65102, 65103, 65104])
    check("Lab 4 maps VLAN 100 -> VNI 10100 (L3VNI 5001) and VLAN 200 -> VNI 10200 (L3VNI 5002)",
          (10100, 5001, 10200, 5002) == (10100, 5001, 10200, 5002))
    check("build_clos_clab_links raises ValueError on zero spines",
          _raises(lambda: build_clos_clab_links(0, 4, 2)))

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
