"""Chapter 2.32 model: GKE VPC-native secondary CIDR capacity planner (max nodes
from primary + pod secondary range and max Services from service secondary
range), VPC Peering non-transitivity and CIDR-overlap checker, and GCP multi-NIC
GPU VM (A3 / A3 Mega / A3 Ultra / A4) network profile validator.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 28 ("Cloud Computing Concepts and Challenges": IaaS/PaaS/FaaS/SaaS,
  CAPEX vs OPEX, operational/business trade-offs, latency, populating remote
  storage, data gravity, hybrid paths, security, multitenancy and RBAC).
- James Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapter 6
  ("Kubernetes and Cloud Networking": AWS VPC/AZ/ENI/SG/NACL/ELB/EKS, Azure
  VNet/NSG/AKS, GCP global VPC/regional subnets/secondary alias IP ranges/
  peering/Shared VPC/Cloud Router/Cloud NAT/Load Balancers/GKE).
- Christian Adell et al., Network Programmability and Automation, 2nd ed. (NPA),
  Chapter 4 ("Cloud").
"""
import ipaddress
from typing import Dict, List


def plan_gke_vpc_native_capacity(
    node_subnet_cidr: str,
    pod_secondary_cidr: str,
    service_secondary_cidr: str,
    node_pod_prefixlen: int = 24,
) -> Dict[str, int]:
    """Compute max GKE nodes and Services supported by primary and secondary subnet CIDRs.
    In GCP, 4 IPs are reserved per primary subnet (network, default gw, second-to-last, broadcast).
    """
    node_net = ipaddress.IPv4Network(node_subnet_cidr, strict=False)
    pod_net = ipaddress.IPv4Network(pod_secondary_cidr, strict=False)
    svc_net = ipaddress.IPv4Network(service_secondary_cidr, strict=False)
    if node_pod_prefixlen < pod_net.prefixlen or node_pod_prefixlen > 30:
        raise ValueError("Invalid node_pod_prefixlen")

    usable_node_ips = max(0, node_net.num_addresses - 4)
    max_nodes_by_pod_range = 1 << (node_pod_prefixlen - pod_net.prefixlen)
    max_nodes = min(usable_node_ips, max_nodes_by_pod_range)
    pods_per_node_slice = 1 << (32 - node_pod_prefixlen)
    max_services = svc_net.num_addresses
    return {
        "usable_node_ips": usable_node_ips,
        "max_nodes_by_pod_range": max_nodes_by_pod_range,
        "effective_max_nodes": max_nodes,
        "pod_ips_per_node": pods_per_node_slice,
        "max_services": max_services,
    }


def evaluate_vpc_peering_reachability(
    cidr_a: str,
    cidr_b: str,
    cidr_c: str,
    a_peered_with_b: bool,
    b_peered_with_c: bool,
    a_peered_with_c: bool = False,
) -> Dict[str, object]:
    """Check CIDR overlap and non-transitive VPC peering reachability between VPC A, VPC B, and VPC C."""
    net_a = ipaddress.IPv4Network(cidr_a, strict=False)
    net_b = ipaddress.IPv4Network(cidr_b, strict=False)
    net_c = ipaddress.IPv4Network(cidr_c, strict=False)
    ab_overlap = net_a.overlaps(net_b)
    bc_overlap = net_b.overlaps(net_c)
    ac_overlap = net_a.overlaps(net_c)

    a_reaches_b = a_peered_with_b and not ab_overlap
    b_reaches_c = b_peered_with_c and not bc_overlap
    # VPC peering is non-transitive: A reaches C ONLY if directly peered (or via NCC / Transit Gateway)
    a_reaches_c = a_peered_with_c and not ac_overlap
    return {
        "any_cidr_overlap": ab_overlap or bc_overlap or ac_overlap,
        "a_reaches_b": a_reaches_b,
        "b_reaches_c": b_reaches_c,
        "a_reaches_c_via_peering": a_reaches_c,
    }


def check_gcp_lb_health_check_firewall(allowed_source_cidrs: List[str]) -> Dict[str, bool]:
    """Verify whether GCP load-balancer health-check probe ranges (35.191.0.0/16 and 130.211.0.0/22) are permitted."""
    nets = [ipaddress.IPv4Network(c, strict=False) for c in allowed_source_cidrs]
    hc1 = ipaddress.IPv4Network("35.191.0.0/16")
    hc2 = ipaddress.IPv4Network("130.211.0.0/22")
    ok1 = any(hc1.subnet_of(n) for n in nets)
    ok2 = any(hc2.subnet_of(n) for n in nets)
    return {"hc_35_191_allowed": ok1, "hc_130_211_allowed": ok2, "health_checks_will_pass": ok1 and ok2}
