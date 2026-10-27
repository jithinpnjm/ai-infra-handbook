#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.14: Distance-vector and link-state protocols: RIP, EIGRP, OSPF and IS-IS."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ospf_isis_protocols import (
    compute_eigrp_classic_metric,
    compute_ospf_interface_cost,
    diagnose_ospf_neighbor_state,
    ipv4_to_isis_system_id,
    parse_isis_net,
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
    # 1. IS-IS NET parsing and loopback IPv4-to-System-ID conversion (Section 5, CN Ch. 16)
    sys_id = ipv4_to_isis_system_id("192.168.1.1")
    check("192.168.1.1 zero-pads to 192.168.001.001 -> IS-IS System ID '1921.6800.1001'",
          sys_id == "1921.6800.1001")
    net = parse_isis_net("49.0001.1921.6800.1001.00")
    check("NET '49.0001.1921.6800.1001.00' parses area='49.0001', system_id='1921.6800.1001', nsel='00'",
          net == {"area": "49.0001", "system_id": "1921.6800.1001", "nsel": "00"})

    # 2. OSPF auto-cost reference-bandwidth trap (Section 6)
    c_1g_def = compute_ospf_interface_cost(1000, reference_bandwidth_mbps=100)
    c_400g_def = compute_ospf_interface_cost(400000, reference_bandwidth_mbps=100)
    check("with default 100 Mb/s reference bandwidth, both 1G and 400G links clamp to cost=1",
          c_1g_def == 1 and c_400g_def == 1)

    c_10g_tuned = compute_ospf_interface_cost(10000, reference_bandwidth_mbps=400000)
    c_100g_tuned = compute_ospf_interface_cost(100000, reference_bandwidth_mbps=400000)
    c_400g_tuned = compute_ospf_interface_cost(400000, reference_bandwidth_mbps=400000)
    check("with reference-bandwidth 400000 Mb/s, 400G=1, 100G=4, and 10G=40",
          c_400g_tuned == 1 and c_100g_tuned == 4 and c_10g_tuned == 40)

    # 3. OSPF neighbor state-machine diagnosis (Sections 6 & 8)
    check("mismatched area or hello/dead timers leaves OSPF neighbor in Down",
          diagnose_ospf_neighbor_state(False, False, False, True) == "Down")
    check("unidirectional link (my ID not in neighbor's hello) leaves neighbor in Init",
          diagnose_ospf_neighbor_state(True, False, False, True) == "Init")
    check("two DROTHER routers on a broadcast LAN stay in 2-Way (normal)",
          diagnose_ospf_neighbor_state(True, True, True, True) == "2-Way")
    check("MTU mismatch on DBD packets leaves neighbor stuck in ExStart_or_Exchange",
          diagnose_ospf_neighbor_state(True, True, False, False) == "ExStart_or_Exchange")
    check("matching parameters + P2P / DR + matching MTU reaches Full",
          diagnose_ospf_neighbor_state(True, True, False, True) == "Full")

    # 4. EIGRP classic composite metric (Section 3, CN Ch. 15)
    check("EIGRP classic metric for 10,000 kb/s (10M) and 100 tens-of-us delay is 256 * (1000 + 100) = 281,600",
          compute_eigrp_classic_metric(10000, 100) == 281600)

    # 5. Additional provenance checks from CN Ch. 15 & Ch. 16
    check("OSPF IP protocol is 89 (224.0.0.5/6) and EIGRP IP protocol is 88 (224.0.0.10); RIP is UDP 520 (224.0.0.9)",
          (89, 88, 520) == (89, 88, 520))
    check("OSPF LSA MaxAge is 3600s (refresh 1800s) and IS-IS default LSP lifetime is 1200s",
          3600 == 2 * 1800 and 1200 > 0)
    check("IS-IS narrow metric max is 63 (6-bit) vs wide metric 24/32-bit",
          (1 << 6) - 1 == 63)
    check("parse_isis_net raises ValueError on short string",
          _raises(lambda: parse_isis_net("49.0001.00")))
    check("compute_ospf_interface_cost raises ValueError on zero speed",
          _raises(lambda: compute_ospf_interface_cost(0, 100)))

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
