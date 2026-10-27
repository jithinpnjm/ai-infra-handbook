"""Chapter 2.12 model: LAG / ECMP flow-hash distribution (layer2 vs layer2+3 vs
layer3+4), modulo-N vs resilient bucket-table remapping fraction on member
removal, LACP active/passive negotiation matrix, and Linux /proc/net/bonding
health check.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 7 ("Packet Switching": equal-cost multipath ECMP, link aggregation,
  hash algorithms, LACP, multichassis link aggregation MLAG, routed parallel
  links).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 4
  ("Supercomputer Hardware": compute/control/login/service nodes,
  compute/control/management/storage/external networks, latency and throughput
  comparisons, tree/fat-tree/hypercube/torus/dragonfly topologies).
"""
import hashlib
from typing import Dict, List, Tuple


def select_bond_member_by_hash(
    flow: Dict[str, object],
    num_members: int,
    policy: str = "layer3+4",
) -> int:
    """Hash a flow according to Linux xmit_hash_policy ('layer2', 'layer2+3', 'layer3+4') into [0, num_members)."""
    if num_members <= 0:
        raise ValueError("num_members must be positive")
    if policy == "layer2":
        key = f"{flow['src_mac']}|{flow['dst_mac']}"
    elif policy == "layer2+3":
        key = f"{flow['src_mac']}|{flow['dst_mac']}|{flow['src_ip']}|{flow['dst_ip']}"
    elif policy == "layer3+4":
        key = f"{flow['src_ip']}|{flow['dst_ip']}|{flow['proto']}|{flow['src_port']}|{flow['dst_port']}"
    else:
        raise ValueError(f"Unsupported hash policy: {policy}")
    digest = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    return digest % num_members


def compare_modulo_vs_resilient_remap_pct(num_members_before: int, num_Flows: int = 1000) -> Dict[str, float]:
    """Compare fraction of flows remapped when 1 of num_members_before fails under plain modulo vs resilient hashing."""
    if num_members_before < 2 or num_Flows <= 0:
        raise ValueError("num_members_before >= 2 and num_Flows > 0 required")
    n_after = num_members_before - 1
    modulo_moved = sum(1 for h in range(num_Flows) if (h % num_members_before) != (h % n_after))
    modulo_pct = round(100.0 * modulo_moved / float(num_Flows), 1)
    # Resilient hashing only moves flows that were on the failed member (1 / N)
    resilient_pct = round(100.0 / float(num_members_before), 1)
    return {
        "modulo_remapped_pct": modulo_pct,
        "resilient_remapped_pct": resilient_pct,
    }


def evaluate_lacp_negotiation(mode_a: str, mode_b: str) -> Dict[str, object]:
    """Determine whether two link ends ('active', 'passive', 'off') form an LACP bundle."""
    valid_modes = {"active", "passive", "off"}
    if mode_a not in valid_modes or mode_b not in valid_modes:
        raise ValueError("Modes must be 'active', 'passive', or 'off'")
    if "off" in {mode_a, mode_b}:
        return {"lacp_up": False, "reason": "one_or_both_sides_not_running_lacp"}
    if mode_a == "passive" and mode_b == "passive":
        return {"lacp_up": False, "reason": "both_sides_passive_neither_initiates_lacpdu"}
    return {"lacp_up": True, "reason": "lacp_negotiated"}


def audit_proc_bonding_status(
    partner_mac: str,
    member_aggregator_ids: List[int],
    active_members: int,
    min_links: int = 1,
) -> Dict[str, object]:
    """Audit /proc/net/bonding/bond0 state for zero partner MAC, mismatched aggregator IDs, and min_links."""
    issues: List[str] = []
    if partner_mac == "00:00:00:00:00:00":
        issues.append("no_lacp_partner_detected_zero_mac")
    if len(set(member_aggregator_ids)) > 1:
        issues.append("mismatched_aggregator_ids_across_members")
    if active_members < min_links:
        issues.append("active_members_below_min_links")
    return {"healthy": len(issues) == 0, "issues": issues}
