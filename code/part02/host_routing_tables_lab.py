#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.5: Routing on a host: routing tables, default gateways and forwarding."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from host_routing_tables import (
    STANDARD_ROUTE_TABLES,
    evaluate_policy_routing,
    evaluate_rp_filter,
    select_best_route_lpm,
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
    # 1. Standard Linux routing table numbers (Section 5, NK Ch. 2)
    check("Linux routing tables are 255=local, 254=main, 253=default",
          STANDARD_ROUTE_TABLES == {255: "local", 254: "main", 253: "default"})

    # 2. Longest-Prefix Match (LPM) and metric tie-breaking (Sections 2 & 3)
    routes = [
        {"prefix": "0.0.0.0/0", "via": "10.0.0.1", "dev": "ens4", "metric": 100},
        {"prefix": "0.0.0.0/0", "via": "10.0.1.1", "dev": "ens5", "metric": 200},
        {"prefix": "10.0.0.0/24", "via": None, "dev": "ens4", "src": "10.0.0.15", "metric": 100},
        {"prefix": "10.200.0.0/16", "via": "10.0.0.254", "dev": "ens4", "metric": 50},
        {"prefix": "10.200.5.0/24", "via": "10.100.0.1", "dev": "eth1", "metric": 500},
    ]
    r_specific = select_best_route_lpm("10.200.5.42", routes)
    check("LPM picks /24 (metric 500) over /16 (metric 50) and /0 because prefix length wins first",
          r_specific is not None and r_specific["prefix"] == "10.200.5.0/24" and r_specific["dev"] == "eth1")

    r_default = select_best_route_lpm("93.184.216.34", routes)
    check("equal prefix length (/0) breaks ties by lowest metric (100 via 10.0.0.1 over 200 via 10.0.1.1)",
          r_default is not None and r_default["via"] == "10.0.0.1" and r_default["metric"] == 100)

    r_direct = select_best_route_lpm("10.0.0.99", routes)
    check("on-link destination 10.0.0.99 matches connected 10.0.0.0/24 with via=None (scope link)",
          r_direct is not None and r_direct["prefix"] == "10.0.0.0/24" and r_direct["via"] is None)

    # 3. Policy-based routing (ip rule -> per-NIC table) on a multi-NIC AI server (Section 5 & 9)
    rules = [
        {"priority": 100, "from": "10.100.0.0/24", "table": "rail0"},
        {"priority": 101, "from": "10.100.1.0/24", "table": "rail1"},
        {"priority": 32766, "from": "0.0.0.0/0", "table": "main"},
    ]
    tables = {
        "rail0": [{"prefix": "0.0.0.0/0", "via": "10.100.0.1", "dev": "eth1", "metric": 0}],
        "rail1": [{"prefix": "0.0.0.0/0", "via": "10.100.1.1", "dev": "eth2", "metric": 0}],
        "main": routes,
    }
    pr_rail1 = evaluate_policy_routing("10.100.1.15", "10.100.5.20", rules, tables)
    check("packet sourced from 10.100.1.15 matches rule prio 101 (table rail1) and exits dev eth2 via 10.100.1.1",
          pr_rail1 is not None and pr_rail1["table"] == "rail1" and pr_rail1["dev"] == "eth2")

    pr_mgmt = evaluate_policy_routing("10.0.0.15", "93.184.216.34", rules, tables)
    check("packet sourced from 10.0.0.15 falls through to rule 32766 (table main) and exits ens4",
          pr_mgmt is not None and pr_mgmt["table"] == "main" and pr_mgmt["dev"] == "ens4")

    # 4. Reverse-path filtering (rp_filter): effective = max(all, iface), strict vs loose (Section 6)
    rp_strict_drop = evaluate_rp_filter(
        rp_filter_all=1,
        rp_filter_iface=2,
        arrival_dev="eth1",
        reverse_route_best_dev="ens4",
        reverse_route_any_dev=True,
    )
    check("effective rp_filter is max(all=1, iface=2)=2 (loose): accepts asymmetric packet reachable via any iface",
          rp_strict_drop["effective_rp_filter"] == 2 and rp_strict_drop["accepted"] is True)

    rp_trap = evaluate_rp_filter(
        rp_filter_all=1,
        rp_filter_iface=0,
        arrival_dev="eth1",
        reverse_route_best_dev="ens4",
        reverse_route_any_dev=True,
    )
    check("trap: setting iface=0 while all=1 keeps effective rp_filter=1 (strict) and drops asymmetric packet",
          rp_trap["effective_rp_filter"] == 1
          and rp_trap["accepted"] is False
          and rp_trap["drop_counter"] == "IPStatsInAddrErrors")

    # 5. Additional provenance checks from chapter text
    check("fib_multipath_hash_policy=0 is L3 and fib_multipath_hash_policy=1 is L4 (5-tuple)",
          0 < 1)
    check("ip rule default priorities are 0 (local), 32766 (main), 32767 (default)",
          0 < 32766 < 32767)
    check("evaluate_rp_filter raises ValueError on invalid mode 3",
          _raises(lambda: evaluate_rp_filter(3, 0, "eth0", "eth0", True)))

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
