"""Chapter 5.13 model: CNI encapsulation MTU & `ping -M do -s` DF payload
calculator, `host-local` / `Whereabouts` IPAM allocator (`ADD` / `DEL`), and
Multus `k8s.v1.cni.cncf.io/networks` secondary RDMA rail interface planner
(`NK` Ch. 3, 4, 6 & `PK` Ch. 5).

Sources modeled:
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK), Chapters 3, 4, and 6:
  * Chapter 3: `ip netns`, `veth` pairs, bridge vs host networking.
  * Chapter 4: CNI specification (`ADD`, `DEL`, `CHECK`, `VERSION`), IPAM JSON.
  * Chapter 6: Cloud subnet node scaling formula `N = 2^(32 - S) - 4` and
    `S = 32 - ceil(log2(N + 4))`, VPC-native vs routes-based clusters.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 5 ("Pod Networking"): overlay vs native
  routing, VXLAN 50-byte encapsulation overhead, WireGuard/IPsec encryption
  trade-offs, `/etc/cni/net.d` and `/opt/cni/bin`.
"""
import ipaddress
import math
from typing import Any, Dict, List, Set, Tuple

ENCAP_OVERHEAD_BYTES: Dict[str, int] = {
    "native": 0,
    "ipip": 20,       # Outer IPv4 (20B)
    "vxlan": 50,      # Outer Eth (14B) + Outer IPv4 (20B) + UDP (8B) + VXLAN (8B) = 50B
    "geneve": 50,     # Base Geneve header (can be larger with TLV options)
    "wireguard": 60,  # Outer IPv4 (20B) + UDP (8B) + WG (32B) = 60B
}


def compute_pod_mtu_and_df_ping(
    underlay_mtu: int,
    encap_mode: str,
    icmp_payload_bytes: int,
) -> Dict[str, object]:
    """Compute inner Pod MTU (`underlay_mtu - encap_overhead`) and whether an
    IPv4 `ping -M do -s <icmp_payload_bytes>` (`+ 20B IP + 8B ICMP = +28B`)
    passes without fragmentation.
    """
    overhead = ENCAP_OVERHEAD_BYTES[encap_mode]
    pod_mtu = underlay_mtu - overhead
    packet_size = icmp_payload_bytes + 28
    return {
        "pod_mtu": pod_mtu,
        "packet_size": packet_size,
        "df_ping_passes": (packet_size <= pod_mtu),
        "max_icmp_payload": pod_mtu - 28,
    }


def compute_subnet_prefix_for_nodes(required_nodes: int) -> int:
    """Model NK Ch. 6 subnet sizing formula:
      N = 2^(32 - S) - 4  =>  S = 32 - ceil(log2(N + 4)).
    """
    return 32 - int(math.ceil(math.log2(required_nodes + 4)))


class CNIHostLocalIPAM:
    """Model Section 3 & 6 `host-local` / `whereabouts` IPAM (`ADD` / `DEL`)."""

    def __init__(self, cidr: str, excluded_cidrs: List[str] | None = None) -> None:
        net = ipaddress.ip_network(cidr)
        excluded: Set[str] = set()
        for ex in excluded_cidrs or []:
            for ip in ipaddress.ip_network(ex):
                excluded.add(str(ip))
        hosts = [str(ip) for ip in net.hosts() if str(ip) not in excluded]
        # First non-excluded host is the gateway (e.g. .1 on bridge)
        self.gateway = hosts[0]
        self.pool = hosts[1:]
        self.allocated: Dict[str, str] = {}  # ip -> container_id

    def add(self, container_id: str) -> str:
        for ip in self.pool:
            if ip not in self.allocated:
                self.allocated[ip] = container_id
                return ip
        raise RuntimeError("CNI IPAM error: failed to allocate for range 0: no IP addresses available in range set")

    def delete(self, container_id: str) -> List[str]:
        freed = [ip for ip, cid in list(self.allocated.items()) if cid == container_id]
        for ip in freed:
            del self.allocated[ip]
        return freed


def plan_multus_pod_interfaces(
    primary_cni: str,
    networks_annotation: str,
) -> List[Dict[str, str]]:
    """Model Section 6 Multus interface attachment order (`eth0` from primary
    CNI, followed by `net1`, `net2`, ... in exact annotation order for GPU rail
    alignment).
    """
    ifaces: List[Dict[str, str]] = [{"ifname": "eth0", "network": primary_cni, "role": "primary"}]
    extra = [n.strip() for n in networks_annotation.split(",") if n.strip()]
    for idx, net_name in enumerate(extra, start=1):
        ifaces.append({"ifname": f"net{idx}", "network": net_name, "role": f"secondary-rail-{idx}"})
    return ifaces
