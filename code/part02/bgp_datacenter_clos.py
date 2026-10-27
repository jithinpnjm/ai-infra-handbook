"""Chapter 2.16 model: RFC 7938 same-spine-ASN valley-free path check, BGP
Link-Bandwidth extended community weighted ECMP (UCMP) traffic share calculator,
Clos spine summarization black-hole and minimum-peers conditional advertisement
checker, and BGP DPF colored session route propagation filter.

Sources modeled:
- Dinakaran Setty et al., AI Data Center Network Design and Technologies
  (ai-data-center-network-design-and-technologies, ADC), Chapter 8 ("IP Routing
  for AI/ML Fabrics": eBGP Clos ASN plans, BGP unnumbered RFC 5549/8950,
  ADD-PATH RFC 7911, AS-PATH normalization, Link Bandwidth extended community
  weighted ECMP 400/800/100/400G, minimum BGP peers per prefix, BGP DPF colored
  sessions, RIFT RFC 9692, IS-IS flood reduction and Flex Algo RFC 9350/9502,
  dragonfly, multi-tenancy, BGP to the server, SRv6/uSID).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 17 (control-plane policy) and Chapter 19 (failure domains, positive
  feedback loops, information hiding, Clos summarization black holes).
"""
from typing import Dict, List, Set


def check_clos_valley_path_rejection(
    spine1_asn: int,
    intermediate_leaf_asn: int,
    spine2_asn: int,
    dest_leaf_asn: int,
) -> Dict[str, object]:
    """Verify whether Spine 2 rejects a valley/hairpin path [intermediate_leaf_asn, spine1_asn, dest_leaf_asn]."""
    as_path_at_spine2 = [intermediate_leaf_asn, spine1_asn, dest_leaf_asn]
    rejected_by_spine2 = spine2_asn in as_path_at_spine2
    return {
        "as_path_seen_by_spine2": as_path_at_spine2,
        "valley_path_rejected": rejected_by_spine2,
        "same_spine_asn": spine1_asn == spine2_asn,
    }


def compute_weighted_ecmp_shares_pct(link_bandwidths_gbps: List[float]) -> List[float]:
    """Compute BGP Link-Bandwidth weighted ECMP (UCMP) traffic shares in percent."""
    if not link_bandwidths_gbps or any(bw <= 0 for bw in link_bandwidths_gbps):
        raise ValueError("link_bandwidths_gbps must be non-empty positive numbers")
    total = float(sum(link_bandwidths_gbps))
    return [round(100.0 * bw / total, 1) for bw in link_bandwidths_gbps]


def evaluate_spine_summary_and_min_peers(
    total_leaves: int,
    reachable_leaves_from_spine: int,
    active_ecmp_peers_for_prefix: int,
    min_peers_required: int = 4,
) -> Dict[str, bool]:
    """Check whether unconditional spine summarization causes a black hole and whether min-peers withdraws a degraded route."""
    summary_causes_blackhole = 0 < reachable_leaves_from_spine < total_leaves
    advertise_under_min_peers = active_ecmp_peers_for_prefix >= min_peers_required
    return {
        "unconditional_summary_blackholes_missing_leaves": summary_causes_blackhole,
        "advertise_prefix_under_min_peers_rule": advertise_under_min_peers,
    }


def filter_dpf_colored_route(
    route_colors: Set[str],
    session_colors: Set[str],
) -> Dict[str, object]:
    """Model BGP DPF colored session advertisement and color pruning (ADC Ch. 8).
    An uncolored route (empty route_colors) matches any session; a colored route
    matches only if route_colors & session_colors is non-empty, pruning unmatched colors.
    """
    if not route_colors:
        return {"advertised": True, "forwarded_colors": set()}
    matched = route_colors & session_colors
    if not matched:
        return {"advertised": False, "forwarded_colors": set()}
    return {"advertised": True, "forwarded_colors": matched}
