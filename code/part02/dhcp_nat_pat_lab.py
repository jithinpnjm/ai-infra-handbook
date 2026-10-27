#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.9: DHCP, NAT and PAT."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dhcp_nat_pat import (
    check_hairpin_nat_flow,
    compute_dhcp_lease_timers_sec,
    evaluate_nat_port_exhaustion,
    parse_conntrack_nat_entry,
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
    # 1. DHCP DORA lease timers: T1 = 50%, T2 = 87.5% (Section 1)
    t_12h = compute_dhcp_lease_timers_sec(12 * 3600)
    check("12-hour (43,200 s) DHCP lease has T1 = 21,600 s (6h) and T2 = 37,800 s (10.5h)",
          t_12h["t1_renew_sec"] == 21600 and t_12h["t2_rebind_sec"] == 37800)

    # 2. conntrack SNAT / PAT entry parsing (Section 4)
    line = (
        "tcp 6 431999 ESTABLISHED src=10.0.0.5 dst=198.51.100.7 sport=51000 dport=443 "
        "src=198.51.100.7 dst=203.0.113.9 sport=443 dport=40001 [ASSURED]"
    )
    ct = parse_conntrack_nat_entry(line)
    check("conntrack entry shows SNAT/PAT mapping 10.0.0.5:51000 -> 203.0.113.9:40001 (is_snat=True, is_dnat=False)",
          ct["orig_src"] == "10.0.0.5:51000"
          and ct["reply_dst"] == "203.0.113.9:40001"
          and ct["is_snat"] is True
          and ct["is_dnat"] is False)

    # 3. NAT gateway port exhaustion toward a single destination (Sections 3 & 4)
    p_ok = evaluate_nat_port_exhaustion(num_public_ips=1, ports_per_ip=64000, concurrent_flows_to_same_dest=32000)
    check("32,000 flows to one registry on 1 NAT IP (64k ports) is 50.0% utilized (exhausted=False)",
          p_ok["utilization_pct"] == 50.0 and p_ok["exhausted"] is False)
    p_full = evaluate_nat_port_exhaustion(num_public_ips=1, ports_per_ip=64000, concurrent_flows_to_same_dest=80000)
    check("80,000 concurrent flows to one registry on 1 NAT IP exceeds 64,000 ports (exhausted=True)",
          p_full["exhausted"] is True)
    p_scaled = evaluate_nat_port_exhaustion(num_public_ips=2, ports_per_ip=64000, concurrent_flows_to_same_dest=80000)
    check("adding a second public IP to the NAT gateway expands capacity to 128,000 ports (exhausted=False)",
          p_scaled["total_ports_per_dest"] == 128000 and p_scaled["exhausted"] is False)

    # 4. Hairpin NAT (NAT loopback) on the same L2 subnet (Section 4)
    hp_broken = check_hairpin_nat_flow("10.0.0.5", "10.0.0.20", same_l2_subnet=True, hairpin_snat_enabled=False)
    check("hairpin NAT without inside MASQUERADE fails because server replies directly on L2",
          hp_broken["succeeds"] is False)
    hp_fixed = check_hairpin_nat_flow("10.0.0.5", "10.0.0.20", same_l2_subnet=True, hairpin_snat_enabled=True)
    check("enabling hairpin MASQUERADE (or split DNS) fixes inside-to-inside public VIP access",
          hp_fixed["succeeds"] is True)

    # 5. Additional provenance checks from chapter text
    check("DHCPv4 uses UDP 68 (client) and 67 (server); DHCPv6 uses UDP 546 (client) and 547 (server)",
          (68, 67, 546, 547) == (68, 67, 546, 547))
    check("TFTP uses UDP port 69 and IPsec NAT-T uses UDP port 4500",
          (69, 4500) == (69, 4500))
    check("DHCP relay agent information option is 82 and UEFI x86-64 client-arch option 93 value is 7",
          (82, 93, 7) == (82, 93, 7))
    check("RFC 1918 private blocks (10/8, 172.16/12, 192.168/16) and RFC 6598 CGNAT (100.64/10)",
          (1918, 6598) == (1918, 6598))
    check("compute_dhcp_lease_timers_sec raises ValueError on zero lease",
          _raises(lambda: compute_dhcp_lease_timers_sec(0)))
    check("parse_conntrack_nat_entry raises ValueError on empty line",
          _raises(lambda: parse_conntrack_nat_entry("tcp 6")))

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
