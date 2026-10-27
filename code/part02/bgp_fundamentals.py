"""Chapter 2.15 model: BGP best-path decision algorithm (Weight -> LOCAL_PREF ->
locally originated -> AS_PATH length -> ORIGIN -> MED -> eBGP over iBGP -> IGP
cost -> router ID), AS_PATH loop detection and allowas-in check, iBGP vs eBGP
advertisement and Route Reflector (ORIGINATOR_ID / CLUSTER_LIST) rules, and
full-mesh iBGP session count n*(n-1)/2.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 16 ("Link State and Path Vector Control Planes": BGP-4 RFC 4271
  history and role as EGP, peering and FSM state machine, best-path decision
  process, advertisement rules, route reflectors RFC 4456) and Chapter 17
  ("Policy in the Control Plane": hot-potato vs cold-potato routing, resource
  segmentation with overlays, elephant 9000B 0.72ms vs mouse 64B 0.05ms on
  100Mb/s link jitter, flow pinning and policy complexity).
"""
from typing import Dict, List


ORIGIN_RANK: Dict[str, int] = {"i": 0, "e": 1, "?": 2}


def select_bgp_best_path(paths: List[Dict[str, object]]) -> Dict[str, object]:
    """Select the winning BGP path using standard best-path tie-breakers."""
    if not paths:
        raise ValueError("paths list must be non-empty")

    def sort_key(p: Dict[str, object]):
        weight = int(p.get("weight", 0))
        local_pref = int(p.get("local_pref", 100))
        local_orig = 1 if bool(p.get("locally_originated", False)) else 0
        as_path_len = len(list(p.get("as_path", [])))
        origin_rank = ORIGIN_RANK.get(str(p.get("origin", "i")), 2)
        med = int(p.get("med", 0))
        is_ebgp = 1 if str(p.get("source_type", "ebgp")) == "ebgp" else 0
        igp_cost = int(p.get("igp_cost", 0))
        peer_router_id = str(p.get("peer_router_id", "255.255.255.255"))
        # Sort ascending: negate attributes where higher wins
        return (
            -weight,
            -local_pref,
            -local_orig,
            as_path_len,
            origin_rank,
            med,
            -is_ebgp,
            igp_cost,
            peer_router_id,
        )

    return sorted(paths, key=sort_key)[0]


def check_as_path_loop(
    local_asn: int,
    as_path: List[int],
    allowas_in_max: int = 0,
) -> Dict[str, object]:
    """Check whether local_asn appears in as_path more than allowas_in_max times."""
    occurrences = sum(1 for asn in as_path if asn == local_asn)
    accepted = occurrences <= allowas_in_max
    return {
        "local_asn_occurrences": occurrences,
        "accepted": accepted,
        "reason": "accepted" if accepted else "rejected_own_asn_in_as_path",
    }


def evaluate_bgp_advertisement_rule(
    learned_from: str,
    target_peer_type: str,
    is_route_reflector: bool = False,
) -> bool:
    """Evaluate BGP split-horizon advertisement rule:
    - Best path learned from eBGP is advertised to both eBGP and iBGP peers.
    - Best path learned from iBGP is advertised to eBGP peers, and to iBGP peers ONLY if Route Reflector.
    """
    if learned_from not in {"ebgp", "ibgp"} or target_peer_type not in {"ebgp", "ibgp"}:
        raise ValueError("Peer types must be 'ebgp' or 'ibgp'")
    if learned_from == "ebgp":
        return True
    if target_peer_type == "ebgp":
        return True
    return is_route_reflector


def compute_ibgp_sessions_full_mesh_vs_rr(num_routers: int, num_route_reflectors: int = 2) -> Dict[str, int]:
    """Compare iBGP session count for a full mesh n*(n-1)//2 vs redundant route reflectors."""
    if num_routers < 2 or num_route_reflectors < 1 or num_route_reflectors >= num_routers:
        raise ValueError("Invalid router or RR count")
    full_mesh = num_routers * (num_routers - 1) // 2
    clients = num_routers - num_route_reflectors
    rr_mesh = num_route_reflectors * (num_route_reflectors - 1) // 2
    rr_total = clients * num_route_reflectors + rr_mesh
    return {"full_mesh_sessions": full_mesh, "rr_sessions": rr_total}
