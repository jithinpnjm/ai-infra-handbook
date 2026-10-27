#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.25: Linux networking IV: namespaces, veth, bridges and container networking."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from container_netns_cni import (
    audit_gpu_pod_rdma_spec,
    evaluate_macvlan_ipvlan_properties,
    resolve_veth_host_peer,
    run_cni_ipam_action,
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
    # 1. CNI ADD / CHECK / DEL lifecycle and host-local IPAM (Section 4)
    allocs = {}
    r1 = run_cni_ipam_action("ADD", "10.244.1.0/24", allocs, container_id="pod-a")
    r2 = run_cni_ipam_action("ADD", "10.244.1.0/24", allocs, container_id="pod-b")
    check("CNI ADD reserves .1 as gateway and assigns 10.244.1.2/24 and 10.244.1.3/24 to pod-a and pod-b",
          r1["gateway"] == "10.244.1.1"
          and r1["address"] == "10.244.1.2/24"
          and r2["address"] == "10.244.1.3/24")
    check("CNI CHECK confirms pod-a is allocated, and CNI DEL releases it",
          run_cni_ipam_action("CHECK", "10.244.1.0/24", allocs, "pod-a")["healthy"] is True
          and run_cni_ipam_action("DEL", "10.244.1.0/24", allocs, "pod-a")["deleted"] is True
          and run_cni_ipam_action("CHECK", "10.244.1.0/24", allocs, "pod-a")["healthy"] is False)

    # 2. Pod veth to host veth peer_ifindex resolution (Section 7)
    host_ifaces = {1: "lo", 2: "eno1", 17: "veth8a9b1c", 18: "cali4f2d9e"}
    check("pod eth0 peer_ifindex=17 maps to host interface 'veth8a9b1c'",
          resolve_veth_host_peer(17, host_ifaces) == "veth8a9b1c")

    # 3. macvlan vs ipvlan L3 properties (Sections 1 & 2)
    mv = evaluate_macvlan_ipvlan_properties("macvlan_bridge")
    ipv = evaluate_macvlan_ipvlan_properties("ipvlan_l3")
    check("macvlan assigns a distinct MAC per container and blocks direct parent-host communication",
          mv["distinct_mac_per_container"] is True and mv["can_talk_to_parent_host_directly"] is False)
    check("ipvlan L3 shares parent MAC and disables L2 broadcast",
          ipv["distinct_mac_per_container"] is False and ipv["l2_broadcast_enabled"] is False)

    # 4. GPU Pod RDMA + Multus spec audit (Section 6)
    pod_ok = audit_gpu_pod_rdma_spec(True, True, nccl_socket_ifname="net1")
    check("GPU pod with Multus annotation + IPC_LOCK capability + NCCL_SOCKET_IFNAME=net1 is ready",
          pod_ok["ready"] is True and pod_ok["issues"] == [])
    pod_bad = audit_gpu_pod_rdma_spec(False, False, nccl_socket_ifname="eth0")
    check("GPU pod missing Multus + missing IPC_LOCK + using primary overlay eth0 flags all 3 issues",
          pod_bad["ready"] is False and len(pod_bad["issues"]) == 3)

    # 5. Additional provenance checks from chapter text
    check("Docker default bridge subnet is 172.17.0.0/16 and Calico link-local gw is 169.254.1.1",
          "172.17.0.0/16".startswith("172.17") and "169.254.1.1".startswith("169.254"))
    check("a /24 node pod CIDR has 254 usable host addresses (256 - 2)", 256 - 2 == 254)
    check("Flannel/Cilium default VXLAN UDP port is 8472 vs IANA 4789", (8472, 4789) == (8472, 4789))
    check("resolve_veth_host_peer raises ValueError on unknown ifindex",
          _raises(lambda: resolve_veth_host_peer(999, host_ifaces)))

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
