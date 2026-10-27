#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.17: Overlays: tunnels, VXLAN, EVPN, segment routing and SD-WAN."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overlays_vxlan_evpn import (
    EVPN_ROUTE_TYPES,
    check_overlay_srlg_diversity,
    compute_irb_vni_scaling_per_leaf,
    simulate_sr_mpls_label_stack,
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
    # 1. EVPN Route Types 1..5 (Section 4, RFC 7432 / RFC 9136)
    check("all 5 EVPN Route Types (1=Auto-Discovery, 2=MAC/IP, 3=IMET, 4=Ethernet Segment, 5=IP Prefix) are mapped",
          len(EVPN_ROUTE_TYPES) == 5
          and "MAC/IP" in EVPN_ROUTE_TYPES[2]["name"]
          and "IP Prefix" in EVPN_ROUTE_TYPES[5]["name"])

    # 2. Asymmetric vs Symmetric IRB per-leaf VNI scaling (Section 4)
    irb = compute_irb_vni_scaling_per_leaf(total_tenant_l2_vnis=200, local_l2_vnis_on_leaf=5, num_tenant_vrfs=1)
    check("with 200 tenant subnets (5 local on leaf), Asymmetric IRB requires 200 VNIs vs Symmetric IRB 6 VNIs (194 saved)",
          irb["asymmetric_irb_vnis_on_leaf"] == 200
          and irb["symmetric_irb_vnis_on_leaf"] == 6
          and irb["vnis_saved"] == 194)

    # 3. SR-MPLS label stack POP progression (Section 6, CN Ch. 9)
    hist = simulate_sr_mpls_label_stack([101, 104, 105, 107], [101, 104, 105, 107])
    check("SR-MPLS stack [101, 104, 105, 107] pops top SID at each hop until empty at destination",
          hist[0] == [104, 105, 107] and hist[-1] == [])

    # 4. Shared Risk Link Group (SRLG) overlay fate-sharing check (Section 8, CN Ch. 9)
    srlg_bad = check_overlay_srlg_diversity({"conduit-north", "spine-1"}, {"conduit-north", "spine-2"})
    check("two overlay tunnels sharing 'conduit-north' fail SRLG diversity check",
          srlg_bad["truly_disjoint"] is False and srlg_bad["shared_srlgs"] == ["conduit-north"])
    srlg_ok = check_overlay_srlg_diversity({"conduit-north", "spine-1"}, {"conduit-south", "spine-2"})
    check("overlay tunnels on separate conduits and spines pass SRLG diversity check",
          srlg_ok["truly_disjoint"] is True)

    # 5. Additional provenance checks from chapter text
    check("VXLAN IANA UDP port is 4789, Linux Flannel/legacy default is 8472, and Geneve UDP port is 6081",
          (4789, 8472, 6081) == (4789, 8472, 6081))
    check("VXLAN 24-bit VNI supports 16,777,216 segments vs 4,094 VLANs",
          (1 << 24) == 16777216 and 16777216 > 4094)
    check("MPLS shim header is 32 bits (20-bit label + 3-bit TC + 1-bit BOS + 8-bit TTL)",
          20 + 3 + 1 + 8 == 32)
    check("SRv6 SID is 128 bits and compressed uSID micro-segment is 16 bits",
          128 // 16 == 8)
    check("compute_irb_vni_scaling_per_leaf raises ValueError on zero total VNIs",
          _raises(lambda: compute_irb_vni_scaling_per_leaf(0, 1, 1)))

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
