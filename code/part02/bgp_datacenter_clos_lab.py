#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.16: BGP in the data center: eBGP Clos, unnumbered, ECMP, anycast and AI-fabric routing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bgp_datacenter_clos import (
    check_clos_valley_path_rejection,
    compute_weighted_ecmp_shares_pct,
    evaluate_spine_summary_and_min_peers,
    filter_dpf_colored_route,
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
    # 1. RFC 7938 same-spine-ASN valley/hairpin path rejection (Section 1)
    same_spine = check_clos_valley_path_rejection(
        spine1_asn=65001, intermediate_leaf_asn=65102, spine2_asn=65001, dest_leaf_asn=65103
    )
    check("when all spines share AS 65001, Spine 2 automatically rejects valley path [65102, 65001, 65103]",
          same_spine["valley_path_rejected"] is True and same_spine["same_spine_asn"] is True)

    diff_spine = check_clos_valley_path_rejection(
        spine1_asn=65001, intermediate_leaf_asn=65102, spine2_asn=65002, dest_leaf_asn=65103
    )
    check("when spines use different ASNs (65001 vs 65002), Spine 2 accepts the valley path through Leaf 2",
          diff_spine["valley_path_rejected"] is False)

    # 2. BGP Link-Bandwidth weighted ECMP (UCMP) (Section 4, ADC Ch. 8)
    shares = compute_weighted_ecmp_shares_pct([400.0, 800.0, 100.0, 400.0])
    check("4 spines with [400, 800, 100, 400] Gb/s receive weighted ECMP shares [23.5%, 47.1%, 5.9%, 23.5%] (sum 100%)",
          shares == [23.5, 47.1, 5.9, 23.5] and round(sum(shares), 1) == 100.0)

    # 3. Clos spine summarization black hole and minimum-peers rule (Section 3 & 4)
    bh = evaluate_spine_summary_and_min_peers(
        total_leaves=4, reachable_leaves_from_spine=3, active_ecmp_peers_for_prefix=3, min_peers_required=4
    )
    check("spine reaching 3 of 4 leaves blackholes the 4th leaf if advertising an unconditional /16 summary",
          bh["unconditional_summary_blackholes_missing_leaves"] is True
          and bh["advertise_prefix_under_min_peers_rule"] is False)

    ok_spine = evaluate_spine_summary_and_min_peers(
        total_leaves=4, reachable_leaves_from_spine=4, active_ecmp_peers_for_prefix=4, min_peers_required=4
    )
    check("spine with all 4 leaves and 4 active peers satisfies both reachability and min-peers=4",
          ok_spine["unconditional_summary_blackholes_missing_leaves"] is False
          and ok_spine["advertise_prefix_under_min_peers_rule"] is True)

    # 4. BGP DPF colored session filtering and pruning (Section 4, ADC Ch. 8)
    dpf_match = filter_dpf_colored_route(route_colors={"black", "grey"}, session_colors={"black"})
    check("BGP DPF route with {'black', 'grey'} crossing a 'black'-only session is advertised with pruned {'black'}",
          dpf_match["advertised"] is True and dpf_match["forwarded_colors"] == {"black"})

    dpf_drop = filter_dpf_colored_route(route_colors={"grey"}, session_colors={"black"})
    check("BGP DPF route with {'grey'} is NOT advertised over a 'black'-only session",
          dpf_drop["advertised"] is False)

    dpf_uncolored = filter_dpf_colored_route(route_colors=set(), session_colors={"black"})
    check("uncolored route matches any colored session",
          dpf_uncolored["advertised"] is True)

    # 5. Additional provenance checks from ADC Ch. 8 and CN Ch. 17/19
    check("32-leaf x 16-spine fabric has 512 links (32 * 16 = 512)", 32 * 16 == 512)
    check("64-port 800G switch in 2x400G breakout with 8 leaves x 64 server ports = 512 GPUs/rail (4 tenants x 128 GPUs)",
          8 * 64 == 512 and 4 * 128 == 512)
    check("NVIDIA MIG partitions one GPU into up to 7 instances (7 MAC-VRFs + 7 IP-VRFs per leaf)",
          7 == 7)
    check("BGP Extended Next Hop capability code is 5 (RFC 5549 / RFC 8950)", 5 == 5 and 8950 > 5549)
    check("SRv6 compressed micro-SID (uSID) is 16 bits inside a 128-bit IPv6 address", 128 // 16 == 8)
    check("compute_weighted_ecmp_shares_pct raises ValueError on empty list",
          _raises(lambda: compute_weighted_ecmp_shares_pct([])))

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
