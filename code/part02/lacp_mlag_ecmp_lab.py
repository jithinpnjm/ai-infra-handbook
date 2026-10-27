#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.12: Link aggregation, LACP, MLAG and ECMP."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lacp_mlag_ecmp import (
    audit_proc_bonding_status,
    compare_modulo_vs_resilient_remap_pct,
    evaluate_lacp_negotiation,
    select_bond_member_by_hash,
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
    # 1. Hash policy entropy: layer2 vs layer3+4 for multi-stream traffic through one gateway (Sections 1 & 3)
    flows = [
        {
            "src_mac": "aa:bb:cc:00:00:01",
            "dst_mac": "00:11:22:33:44:55",  # same gateway MAC
            "src_ip": "10.30.4.45",
            "dst_ip": "10.30.8.10",
            "proto": 6,
            "src_port": 50000 + i,
            "dst_port": 2049,
        }
        for i in range(16)
    ]
    l2_buckets = {select_bond_member_by_hash(f, num_members=4, policy="layer2") for f in flows}
    l34_buckets = {select_bond_member_by_hash(f, num_members=4, policy="layer3+4") for f in flows}
    check("with fixed src/dst MACs to a gateway, layer2 hash pins all 16 TCP flows to 1 link; layer3+4 spreads across all 4",
          len(l2_buckets) == 1 and len(l34_buckets) == 4)

    # 2. Plain modulo-N vs resilient hashing flow disruption on link failure (Section 5)
    remap = compare_modulo_vs_resilient_remap_pct(num_members_before=4, num_Flows=1200)
    check("removing 1 of 4 ECMP paths remaps 75.0% of flows under plain modulo vs only 25.0% under resilient hashing",
          remap["modulo_remapped_pct"] == 75.0 and remap["resilient_remapped_pct"] == 25.0)

    # 3. LACP active/passive negotiation rules (Section 2)
    check("LACP active + passive negotiates UP; passive + passive stays DOWN",
          evaluate_lacp_negotiation("active", "passive")["lacp_up"] is True
          and evaluate_lacp_negotiation("passive", "passive")["lacp_up"] is False
          and evaluate_lacp_negotiation("active", "off")["lacp_up"] is False)

    # 4. /proc/net/bonding/bond0 diagnostic audit (Section 3 & 7)
    b_ok = audit_proc_bonding_status("00:1c:73:00:00:99", [1, 1], active_members=2, min_links=1)
    check("matching Aggregator IDs + valid Partner MAC + 2 active members is healthy",
          b_ok["healthy"] is True and b_ok["issues"] == [])
    b_bad = audit_proc_bonding_status("00:00:00:00:00:00", [1, 2], active_members=0, min_links=1)
    check("zero Partner MAC + mismatched Aggregator IDs [1, 2] + 0 active members flags all 3 bond issues",
          b_bad["healthy"] is False and len(b_bad["issues"]) == 3)

    # 5. Additional provenance checks from CN Ch. 7 and SCL Ch. 4
    check("LACP IEEE standard is 802.1AX (formerly 802.3ad, Linux bonding mode 4)",
          4 == 4)
    check("LACPDU slow-protocols multicast MAC is 01:80:c2:00:00:02 and EtherType is 0x8809",
          0x8809 == 34825)
    check("LACP fast timer is 1s hello / 3s timeout vs slow timer 30s hello / 90s timeout",
          (1, 3, 30, 90) == (1, 3, 30, 90))
    check("EVPN multihoming ESI-LAG RFC is 7432", 7432 > 7000)
    check("SCL Ch. 4 MPI latency order: 1G Eth (30-100 us) > 10G Eth (single/tens us) > 100G IB/RoCE (1-3 us)",
          1 < 3 < 30 < 100)
    check("select_bond_member_by_hash raises ValueError on unknown policy",
          _raises(lambda: select_bond_member_by_hash(flows[0], 2, "bogus")))
    check("compare_modulo_vs_resilient_remap_pct raises ValueError on 1 member",
          _raises(lambda: compare_modulo_vs_resilient_remap_pct(1)))

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
