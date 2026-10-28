"""Chapter 5.14 model: BGP session scaling calculator (Full-Mesh vs Route
Reflectors vs eBGP ToR Peering), Calico `CrossSubnet` encapsulation selector,
Cilium numeric Security Identity vs IP-based rule scaling calculator, and
multi-homed GPU node interface selector (`PK` Ch. 5 & `NK` Ch. 4–6).

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 5 ("Pod Networking"): overlay vs native
  BGP routing, Calico BGP route distribution, Cilium eBPF datapath, encryption.
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK), Chapters 4–6 (CNI implementations, Cilium eBPF, cloud CNI).
"""
import ipaddress
from typing import Dict, List, Mapping, Sequence, Tuple


def compute_bgp_session_counts(
    node_count: int,
    route_reflector_count: int = 3,
    tor_uplinks_per_node: int = 2,
) -> Dict[str, int]:
    """Model Section 3 BGP peering topologies across `node_count` nodes:
    - `full_mesh_sessions`: N * (N - 1) // 2 cluster-wide sessions (N - 1 per node).
    - `route_reflector_sessions`: each non-RR node peers with `R` route reflectors
      plus R*(R-1)//2 between RRs (`R` sessions per worker node).
    - `tor_ebgp_sessions`: each node peers only with its local ToR switch(es)
      (`tor_uplinks_per_node` per node).
    """
    full_mesh = (node_count * (node_count - 1)) // 2
    rr_workers = max(0, node_count - route_reflector_count)
    rr_total = rr_workers * route_reflector_count + (route_reflector_count * (route_reflector_count - 1)) // 2
    tor_total = node_count * tor_uplinks_per_node
    return {
        "full_mesh_total_sessions": full_mesh,
        "full_mesh_per_node": node_count - 1,
        "route_reflector_total_sessions": rr_total,
        "route_reflector_per_worker": route_reflector_count,
        "tor_ebgp_total_sessions": tor_total,
        "tor_ebgp_per_node": tor_uplinks_per_node,
    }


def select_calico_cross_subnet_mode(
    src_node_ip: str,
    dst_node_ip: str,
    node_subnet_cidr: str,
    encap_proto: str = "ipip",
) -> str:
    """Model Section 2 & 3 Calico `CrossSubnet` mode: route natively without
    encapsulation when both nodes share the same L2 subnet (`node_subnet_cidr`),
    and encapsulate (`ipip` or `vxlan`) only when crossing an L3 router boundary.
    """
    subnet = ipaddress.ip_network(node_subnet_cidr)
    if ipaddress.ip_address(src_node_ip) in subnet and ipaddress.ip_address(dst_node_ip) in subnet:
        return "native_routed"
    return f"encapsulated_{encap_proto}"


def compare_policy_scaling_ip_vs_identity(
    source_pods: int,
    dest_pods: int,
    unique_source_label_sets: int = 1,
    unique_dest_label_sets: int = 1,
) -> Dict[str, int]:
    """Model Section 4 Cilium label-derived Security Identity map entries vs
    naive IP-pair rule expansion.
    """
    return {
        "ip_pair_combinations": source_pods * dest_pods,
        "cilium_identity_map_entries": unique_source_label_sets * unique_dest_label_sets,
    }


def select_primary_cni_node_interface(
    interfaces: Sequence[Mapping[str, str]],
    exclude_prefixes: Tuple[str, ...] = ("rdma", "ib", "ens1f", "mlx", "cali", "cilium", "veth", "docker"),
) -> str:
    """Model Section 6 multi-homed GPU node IP autodetection: pick the management
    interface and explicitly exclude RDMA/RoCE/virtual interfaces.
    """
    for iface in interfaces:
        name = str(iface["name"])
        if not name.startswith(exclude_prefixes) and iface.get("ip"):
            return name
    raise RuntimeError("no suitable management interface found for primary CNI")
