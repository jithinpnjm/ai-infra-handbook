"""Chapter 2.25 model: CNI ADD/DEL/CHECK lifecycle and host-local IPAM simulator,
veth peer_ifindex mapper between container netns and host netns, macvlan vs
ipvlan L2/L3 parent-reachability evaluator, and GPU pod Multus + NCCL RDMA
configuration auditor.

Sources modeled:
- James Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapters 2
  and 3 ("Container Networking Basics": hypervisors vs containers, OCI/LXC/runc/
  containerd/CRI-O, Docker CNM sandbox/endpoint/network, bridge/host/none/macvlan/
  ipvlan/overlay, CNI ADD/DEL/CHECK and chained plugins, Flannel/Calico/Cilium/
  AWS VPC CNI).
- Josh Rosso et al., Production Kubernetes (PK), Chapter 5 ("Pod Networking").
- nvidia-devops/volume-01/03-linux-networking-masterclass.md.
"""
import ipaddress
from typing import Dict, List


def run_cni_ipam_action(
    command: str,
    subnet_cidr: str,
    allocated_ips: Dict[str, str],
    container_id: str,
    ifname: str = "eth0",
) -> Dict[str, object]:
    """Simulate CNI ADD, DEL, and CHECK with a host-local subnet allocator."""
    net = ipaddress.IPv4Network(subnet_cidr, strict=False)
    hosts = list(net.hosts())
    gateway_ip = str(hosts[0])
    usable_pool = [str(ip) for ip in hosts[1:]]

    if command == "ADD":
        if container_id in allocated_ips:
            assigned = allocated_ips[container_id]
        else:
            used = set(allocated_ips.values())
            avail = [ip for ip in usable_pool if ip not in used]
            if not avail:
                raise ValueError("IPAM subnet exhausted")
            assigned = avail[0]
            allocated_ips[container_id] = assigned
        return {
            "cniVersion": "1.0.0",
            "ifname": ifname,
            "address": f"{assigned}/{net.prefixlen}",
            "gateway": gateway_ip,
        }
    if command == "DEL":
        allocated_ips.pop(container_id, None)
        return {"deleted": True}
    if command == "CHECK":
        return {"healthy": container_id in allocated_ips}
    raise ValueError(f"Unsupported CNI_COMMAND: {command}")


def resolve_veth_host_peer(
    pod_eth0_peer_ifindex: int,
    host_interfaces_by_ifindex: Dict[int, str],
) -> str:
    """Resolve the host-side veth interface name from the pod's ethtool -S peer_ifindex."""
    if pod_eth0_peer_ifindex not in host_interfaces_by_ifindex:
        raise ValueError(f"ifindex {pod_eth0_peer_ifindex} not found on host")
    return host_interfaces_by_ifindex[pod_eth0_peer_ifindex]


def evaluate_macvlan_ipvlan_properties(driver_mode: str) -> Dict[str, object]:
    """Return MAC uniqueness and default host-parent reachability for macvlan_bridge vs ipvlan_l3."""
    if driver_mode == "macvlan_bridge":
        return {
            "distinct_mac_per_container": True,
            "can_talk_to_parent_host_directly": False,
            "l2_broadcast_enabled": True,
        }
    if driver_mode == "ipvlan_l3":
        return {
            "distinct_mac_per_container": False,
            "can_talk_to_parent_host_directly": False,
            "l2_broadcast_enabled": False,
        }
    raise ValueError(f"Unsupported mode: {driver_mode}")


def audit_gpu_pod_rdma_spec(
    has_multus_networks_annotation: bool,
    has_ipc_lock_capability: bool,
    nccl_socket_ifname: str,
) -> Dict[str, object]:
    """Audit a Kubernetes GPU training Pod spec for RDMA and Multus readiness."""
    issues: List[str] = []
    if not has_multus_networks_annotation:
        issues.append("missing_multus_network_attachment_annotation")
    if not has_ipc_lock_capability:
        issues.append("missing_IPC_LOCK_capability_for_rdma_memory_pinning")
    if nccl_socket_ifname == "eth0":
        issues.append("nccl_socket_ifname_set_to_primary_overlay_eth0")
    return {"ready": len(issues) == 0, "issues": issues}
