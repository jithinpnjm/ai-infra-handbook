#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.13: Pod networking under the hood: veth, bridges, routes and CNI plugins."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cni_pod_networking_sim import (
    CNIHostLocalIPAM,
    compute_pod_mtu_and_df_ping,
    compute_subnet_prefix_for_nodes,
    plan_multus_pod_interfaces,
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
    # 1. Section 5 & PK Ch. 5: VXLAN 50-byte MTU math and ping -M do -s 1422 vs 1423
    ok_1422 = compute_pod_mtu_and_df_ping(1500, "vxlan", 1422)
    fail_1423 = compute_pod_mtu_and_df_ping(1500, "vxlan", 1423)
    wg_1500 = compute_pod_mtu_and_df_ping(1500, "wireguard", 1412)
    check(
        "VXLAN on 1500 underlay gives pod_mtu=1450 (max ICMP payload 1422B); WireGuard gives pod_mtu=1440; NK Ch. 6 250 nodes needs /24",
        ok_1422["pod_mtu"] == 1450
        and ok_1422["df_ping_passes"] is True
        and fail_1423["df_ping_passes"] is False
        and wg_1500["pod_mtu"] == 1440
        and compute_subnet_prefix_for_nodes(250) == 24,
    )

    # 2. Section 3 & 6: host-local / Whereabouts IPAM allocation, exclusion, exhaustion, and DEL cleanup
    ipam = CNIHostLocalIPAM("192.168.10.0/29", excluded_cidrs=["192.168.10.0/30"])
    # /29 has .1..6; excluding .0/30 removes .1, .2, .3; .4 is gateway -> .5 and .6 are allocatable
    ip1 = ipam.add("sb-1")
    ip2 = ipam.add("sb-2")
    exhausted = False
    try:
        ipam.add("sb-3")
    except RuntimeError:
        exhausted = True
    freed = ipam.delete("sb-1")
    ip3 = ipam.add("sb-3")
    check(
        "CNIHostLocalIPAM honors excluded range, allocates .5 and .6, raises on exhaustion, and reuses .5 after CNI DEL",
        ip1 == "192.168.10.5"
        and ip2 == "192.168.10.6"
        and exhausted is True
        and freed == ["192.168.10.5"]
        and ip3 == "192.168.10.5",
    )

    # 3. Section 6: Multus secondary RDMA rail interface ordering
    ifaces = plan_multus_pod_interfaces("calico", "rdma-net-a, rdma-net-b")
    check(
        "plan_multus_pod_interfaces attaches eth0 (calico), net1 (rdma-net-a), and net2 (rdma-net-b) in deterministic rail order",
        [i["ifname"] for i in ifaces] == ["eth0", "net1", "net2"]
        and ifaces[1]["network"] == "rdma-net-a"
        and ifaces[2]["network"] == "rdma-net-b",
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
