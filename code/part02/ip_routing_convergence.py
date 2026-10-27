"""Chapter 2.13 model: Administrative Distance (AD) route source selection,
DUAL feasibility condition (RD < FD) and Loop-Free Alternate (LFA) inequality
(dist(N, D) < dist(N, S) + dist(S, D)), Dijkstra SPF shortest-path solver, and
convergence timeline breakdown.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 11 (redistribution metrics and loops), Chapter 12 (trees, LFA,
  waterfall model, P/Q space, rLFA, Bellman-Ford 1955-1958, DUAL), Chapter 13
  (Dijkstra SPF 1959, partial/incremental SPF, path vector, Suurballe disjoint
  paths, MRT), and Chapter 14 (polling vs event-driven detection, BFD, CAP
  theorem in routing, convergence and micro-loops).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9.
"""
import heapq
from typing import Dict, List, Optional, Tuple


DEFAULT_ADMIN_DISTANCE: Dict[str, int] = {
    "connected": 0,
    "static": 1,
    "ebgp": 20,
    "eigrp": 90,
    "ospf": 110,
    "isis": 115,
    "rip": 120,
    "ibgp": 200,
}


def select_route_by_admin_distance(candidates: List[Dict[str, object]]) -> Dict[str, object]:
    """Select the winning route for the same prefix by lowest Administrative Distance, then lowest metric."""
    if not candidates:
        raise ValueError("candidates must be non-empty")
    return sorted(candidates, key=lambda c: (int(c["ad"]), int(c["metric"])))[0]


def check_dual_and_lfa_conditions(
    dist_s_to_d: int,
    dist_s_to_n: int,
    dist_n_to_d: int,
) -> Dict[str, bool]:
    """Evaluate DUAL feasibility condition (RD < FD: dist_n_to_d < dist_s_to_d)
    and LFA loop-free condition (dist_n_to_d < dist_n_to_s + dist_s_to_d).
    """
    if dist_s_to_d <= 0 or dist_s_to_n <= 0 or dist_n_to_d < 0:
        raise ValueError("Distances must be positive")
    dual_feasible_successor = dist_n_to_d < dist_s_to_d
    lfa_loop_free = dist_n_to_d < (dist_s_to_n + dist_s_to_d)
    return {
        "dual_feasible_successor": dual_feasible_successor,
        "lfa_loop_free": lfa_loop_free,
        "lfa_downstream": dual_feasible_successor,
    }


def run_dijkstra_spf(
    adj: Dict[str, List[Tuple[str, int]]],
    root: str,
) -> Dict[str, Dict[str, object]]:
    """Run Dijkstra's SPF from root and return shortest cost and first-hop set (ECMP) per node."""
    if root not in adj:
        raise ValueError(f"Root {root} not in graph")
    dist: Dict[str, int] = {root: 0}
    first_hops: Dict[str, List[str]] = {root: []}
    pq: List[Tuple[int, str]] = [(0, root)]

    while pq:
        d_u, u = heapq.heappop(pq)
        if d_u > dist.get(u, 1 << 60):
            continue
        for v, w in adj.get(u, []):
            if w <= 0:
                raise ValueError("Link weights must be positive")
            nd = d_u + w
            nh = [v] if u == root else list(first_hops[u])
            if nd < dist.get(v, 1 << 60):
                dist[v] = nd
                first_hops[v] = sorted(set(nh))
                heapq.heappush(pq, (nd, v))
            elif nd == dist.get(v, 1 << 60):
                first_hops[v] = sorted(set(first_hops[v]) | set(nh))

    return {
        node: {"cost": dist[node], "first_hops": first_hops[node]}
        for node in sorted(dist.keys())
    }


def compute_convergence_total_ms(
    detection_ms: float,
    origination_throttle_ms: float,
    flooding_propagation_ms: float,
    spf_compute_ms: float,
    fib_programming_ms: float,
) -> Dict[str, float]:
    """Sum the 5 stages of control-plane convergence and identify the dominant stage."""
    stages = {
        "detection": detection_ms,
        "origination": origination_throttle_ms,
        "propagation": flooding_propagation_ms,
        "compute": spf_compute_ms,
        "fib_install": fib_programming_ms,
    }
    if any(v < 0 for v in stages.values()):
        raise ValueError("Stage durations must be non-negative")
    total = round(sum(stages.values()), 1)
    dominant = max(stages.items(), key=lambda kv: kv[1])[0]
    return {"total_ms": total, "dominant_stage": dominant}
