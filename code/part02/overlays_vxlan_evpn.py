"""Chapter 2.17 model: EVPN Route Types 1..5 mapper, Asymmetric vs Symmetric IRB
per-leaf VNI state scaling calculator, SR-MPLS label stack (PUSH / POP / CONTINUE)
stepper, and Shared Risk Link Group (SRLG) overlay disjointness checker.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 9 ("Network Virtualization": tunnels, overlays, underlays, VRFs,
  Ethernet over IP, virtual private access, segment routing SR-MPLS and SRv6,
  SD-WAN, interaction surfaces, Shared Risk Link Groups SRLGs, overlaid control
  planes).
- Dinakaran Setty et al., AI Data Center Network Design and Technologies (ADC),
  Chapter 8 (EVPN-VXLAN multi-tenancy, GBP, SRv6/uSID).
- James Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapter 3
  (container networking overlays, VXLAN, Geneve, IPIP).
"""
from typing import Dict, List, Set


EVPN_ROUTE_TYPES: Dict[int, Dict[str, str]] = {
    1: {"name": "Ethernet Auto-Discovery", "role": "Multihoming fast convergence and aliasing per ES/EVI"},
    2: {"name": "MAC/IP Advertisement", "role": "Host MAC and IP reachability, ARP suppression, MAC mobility sequence"},
    3: {"name": "Inclusive Multicast Ethernet Tag", "role": "BUM replication list discovery per VNI"},
    4: {"name": "Ethernet Segment", "role": "Designated Forwarder (DF) election among multihomed leaves sharing an ESI"},
    5: {"name": "IP Prefix", "role": "Inter-subnet / external IP prefix advertisement into tenant IP-VRFs"},
}


def compute_irb_vni_scaling_per_leaf(
    total_tenant_l2_vnis: int,
    local_l2_vnis_on_leaf: int,
    num_tenant_vrfs: int = 1,
) -> Dict[str, int]:
    """Compare VNI state required on a leaf under Asymmetric IRB (all L2 VNIs) vs Symmetric IRB (local L2 VNIs + L3 VNI)."""
    if total_tenant_l2_vnis <= 0 or local_l2_vnis_on_leaf < 0 or num_tenant_vrfs <= 0:
        raise ValueError("Invalid IRB VNI parameters")
    asymmetric_vnis = total_tenant_l2_vnis
    symmetric_vnis = local_l2_vnis_on_leaf + num_tenant_vrfs
    return {
        "asymmetric_irb_vnis_on_leaf": asymmetric_vnis,
        "symmetric_irb_vnis_on_leaf": symmetric_vnis,
        "vnis_saved": max(0, asymmetric_vnis - symmetric_vnis),
    }


def simulate_sr_mpls_label_stack(
    initial_stack: List[int],
    hop_owned_sids: List[int],
) -> List[List[int]]:
    """Simulate SR-MPLS label stack after each hop pops its owned Node/Adjacency SID from the top of stack."""
    stack = list(initial_stack)
    history: List[List[int]] = []
    for sid in hop_owned_sids:
        while stack and stack[0] == sid:
            stack.pop(0)  # POP operation
        history.append(list(stack))
    return history


def check_overlay_srlg_diversity(
    tunnel_a_underlay_srlgs: Set[str],
    tunnel_b_underlay_srlgs: Set[str],
) -> Dict[str, object]:
    """Check whether two logically redundant overlay tunnels share any physical underlay Shared Risk Link Group (SRLG)."""
    shared = sorted(tunnel_a_underlay_srlgs & tunnel_b_underlay_srlgs)
    return {
        "truly_disjoint": len(shared) == 0,
        "shared_srlgs": shared,
    }
