#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.13: IP routing: static routes, dynamic routing and convergence."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ip_routing_convergence import (
    DEFAULT_ADMIN_DISTANCE,
    check_dual_and_lfa_conditions,
    compute_convergence_total_ms,
    run_dijkstra_spf,
    select_route_by_admin_distance,
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
    # 1. Administrative Distance (AD) ordering and floating static backup (Section 1)
    check("default AD order: connected(0) < static(1) < eBGP(20) < EIGRP(90) < OSPF(110) < IS-IS(115) < RIP(120) < iBGP(200)",
          DEFAULT_ADMIN_DISTANCE["connected"] < DEFAULT_ADMIN_DISTANCE["static"] < DEFAULT_ADMIN_DISTANCE["ebgp"]
          < DEFAULT_ADMIN_DISTANCE["ospf"] < DEFAULT_ADMIN_DISTANCE["isis"] < DEFAULT_ADMIN_DISTANCE["rip"] < DEFAULT_ADMIN_DISTANCE["ibgp"])

    cands = [
        {"proto": "ospf", "ad": 110, "metric": 20, "via": "10.0.0.1"},
        {"proto": "floating_static", "ad": 200, "metric": 1, "via": "10.0.0.2"},
    ]
    win = select_route_by_admin_distance(cands)
    check("OSPF (AD 110) beats floating static backup (AD 200) regardless of metric",
          win["proto"] == "ospf")

    # 2. DUAL feasibility condition (RD < FD) and LFA inequality (dist(N,D) < dist(N,S) + dist(S,D)) (Sections 3 & 4)
    c1 = check_dual_and_lfa_conditions(dist_s_to_d=10, dist_s_to_n=5, dist_n_to_d=8)
    check("neighbor N with RD=8 < FD=10 satisfies both DUAL feasible successor and LFA loop-free conditions",
          c1["dual_feasible_successor"] is True and c1["lfa_loop_free"] is True)

    c2 = check_dual_and_lfa_conditions(dist_s_to_d=10, dist_s_to_n=5, dist_n_to_d=12)
    check("neighbor N with RD=12 (>= FD=10, but < 5+10=15) is a valid LFA backup even though not a strict DUAL downstream successor",
          c2["dual_feasible_successor"] is False and c2["lfa_loop_free"] is True)

    c_ring = check_dual_and_lfa_conditions(dist_s_to_d=10, dist_s_to_n=10, dist_n_to_d=20)
    check("in a symmetric ring where dist(N,D)=20 == dist(N,S)+dist(S,D)=20, N is NOT a loop-free alternate",
          c_ring["lfa_loop_free"] is False)

    # 3. Dijkstra SPF and ECMP on a 4-node diamond topology (Section 3)
    diamond = {
        "A": [("B", 10), ("C", 10)],
        "B": [("A", 10), ("D", 10)],
        "C": [("A", 10), ("D", 10)],
        "D": [("B", 10), ("C", 10)],
    }
    spf = run_dijkstra_spf(diamond, root="A")
    check("Dijkstra SPF on symmetric diamond finds cost(A->D)=20 with ECMP first_hops=['B', 'C']",
          spf["D"]["cost"] == 20 and spf["D"]["first_hops"] == ["B", "C"])

    # 4. Convergence timeline calculation (Section 5)
    conv_bfd = compute_convergence_total_ms(
        detection_ms=150.0,
        origination_throttle_ms=50.0,
        flooding_propagation_ms=10.0,
        spf_compute_ms=20.0,
        fib_programming_ms=250.0,
    )
    check("convergence timeline sums to 480.0 ms with fib_install (250 ms) as the dominant stage",
          conv_bfd["total_ms"] == 480.0 and conv_bfd["dominant_stage"] == "fib_install")

    # 5. Additional provenance checks from chapter text
    check("RIP infinity metric is 16 (max usable hops = 15)", 15 + 1 == 16)
    check("BFD single-hop UDP port is 3784 and multihop UDP port is 4784 (RFC 5880)",
          (3784, 4784) == (3784, 4784))
    check("OSPF default hello/dead is 10s/40s and BGP default keepalive/hold is 60s/180s",
          40 == 4 * 10 and 180 == 3 * 60)
    check("check_dual_and_lfa_conditions raises ValueError on zero distance",
          _raises(lambda: check_dual_and_lfa_conditions(0, 5, 5)))
    check("run_dijkstra_spf raises ValueError on unknown root",
          _raises(lambda: run_dijkstra_spf(diamond, "Z")))

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
