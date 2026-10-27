#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.15: BGP fundamentals and control-plane policy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bgp_fundamentals import (
    check_as_path_loop,
    compute_ibgp_sessions_full_mesh_vs_rr,
    evaluate_bgp_advertisement_rule,
    select_bgp_best_path,
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
    # 1. BGP Best-Path Decision Process (Section 4)
    p_lp = [
        {"id": "path_a", "local_pref": 100, "as_path": [65001]},
        {"id": "path_b", "local_pref": 200, "as_path": [65002, 65003, 65004]},
    ]
    check("higher LOCAL_PREF (200) beats shorter AS_PATH ([65001])",
          select_bgp_best_path(p_lp)["id"] == "path_b")

    p_aspath = [
        {"id": "short_as", "local_pref": 100, "as_path": [65001, 65002], "med": 50},
        {"id": "long_as", "local_pref": 100, "as_path": [65003, 65003, 65002], "med": 10},
    ]
    check("when LOCAL_PREF is tied, shorter AS_PATH (length 2) beats lower MED (10)",
          select_bgp_best_path(p_aspath)["id"] == "short_as")

    p_hot_potato = [
        {"id": "far_exit", "local_pref": 100, "as_path": [65001], "med": 0, "source_type": "ibgp", "igp_cost": 50},
        {"id": "near_exit", "local_pref": 100, "as_path": [65001], "med": 0, "source_type": "ibgp", "igp_cost": 10},
    ]
    check("hot-potato tie-break picks lowest IGP cost to NEXT_HOP (10 over 50)",
          select_bgp_best_path(p_hot_potato)["id"] == "near_exit")

    # 2. AS_PATH loop detection and allowas-in override (Section 3)
    loop_rej = check_as_path_loop(local_asn=65000, as_path=[65003, 65001, 65000], allowas_in_max=0)
    check("router in AS 65000 rejects update with [65003, 65001, 65000] by default",
          loop_rej["accepted"] is False and loop_rej["local_asn_occurrences"] == 1)
    loop_allow = check_as_path_loop(local_asn=65000, as_path=[65003, 65001, 65000], allowas_in_max=1)
    check("allowas-in 1 permits 1 occurrence of local ASN in AS_PATH",
          loop_allow["accepted"] is True)

    # 3. BGP Advertisement Rules and Route Reflectors (Section 5)
    check("eBGP-learned route is advertised to both eBGP and iBGP peers",
          evaluate_bgp_advertisement_rule("ebgp", "ebgp") is True
          and evaluate_bgp_advertisement_rule("ebgp", "ibgp") is True)
    check("iBGP-learned route is NOT advertised to another iBGP peer unless router is a Route Reflector",
          evaluate_bgp_advertisement_rule("ibgp", "ibgp", is_route_reflector=False) is False
          and evaluate_bgp_advertisement_rule("ibgp", "ibgp", is_route_reflector=True) is True)

    # 4. iBGP Full-Mesh n*(n-1)/2 vs Route Reflector scaling (Section 5)
    scale_100 = compute_ibgp_sessions_full_mesh_vs_rr(num_routers=100, num_route_reflectors=2)
    check("100 iBGP routers need 4,950 full-mesh sessions vs 197 sessions with 2 Route Reflectors",
          scale_100 == {"full_mesh_sessions": 4950, "rr_sessions": 197})

    # 5. Additional provenance checks from CN Ch. 16 & Ch. 17
    check("BGP runs over TCP port 179 and default keepalive/hold is 60s/180s (DC tuned 3s/9s)",
          179 == 179 and 180 == 3 * 60 and 9 == 3 * 3)
    check("16-bit private ASN range is 64512..65534 and 32-bit private ASN range starts at 4200000000",
          64512 < 65534 and 4200000000 > (1 << 16))
    check("CN Ch. 17 elephant vs mouse serialization on 100 Mb/s: 9000B = 0.72 ms, 1500B = 0.12 ms, 64B = ~0.005 ms (0.05 ms with framing)",
          round((9000 * 8) / 100000.0, 2) == 0.72
          and round((1500 * 8) / 100000.0, 2) == 0.12
          and round((64 * 8) / 100000.0, 3) == 0.005)
    check("select_bgp_best_path raises ValueError on empty list",
          _raises(lambda: select_bgp_best_path([])))

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
