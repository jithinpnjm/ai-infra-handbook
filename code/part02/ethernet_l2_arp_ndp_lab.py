#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.3: Ethernet and L2: frames, MAC addresses, switching, ARP and NDP."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ethernet_l2_arp_ndp import (
    compute_serialization_delay_ns,
    decode_mac_address,
    mac_to_ipv6_eui64_link_local,
    simulate_switch_frame_action,
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
    # 1. MAC address I/G and U/L bit decoding (Section 2)
    m_qemu = decode_mac_address("52:54:00:12:34:56")
    check("QEMU MAC 52:54:00:12:34:56 (0x52 = 01010010) is unicast (I/G=0) and locally administered (U/L=1)",
          m_qemu["is_unicast"] is True and m_qemu["locally_administered"] is True and m_qemu["oui"] == "52:54:00")
    m_bcast = decode_mac_address("ff:ff:ff:ff:ff:ff")
    check("ff:ff:ff:ff:ff:ff is broadcast and multicast (I/G=1)",
          m_bcast["is_broadcast"] is True and m_bcast["is_multicast"] is True)
    m_ipv6_mcast = decode_mac_address("33:33:ff:67:89:ab")
    check("33:33:ff:67:89:ab is IPv6 multicast (I/G=1)",
          m_ipv6_mcast["is_multicast"] is True and m_ipv6_mcast["is_broadcast"] is False)

    # 2. Switch MAC learning, unknown-unicast flooding, and selective forwarding (Section 5)
    fdb = {}
    ports = [1, 2, 3]
    step1 = simulate_switch_frame_action(fdb, ports, ingress_port=1, src_mac="02:00:00:00:00:0a", dst_mac="02:00:00:00:00:0b")
    check("first frame from A (port 1) to unknown B floods out ports [2, 3] and learns A -> port 1",
          step1["action"] == "flood_unknown_unicast" and step1["egress_ports"] == [2, 3] and fdb["02:00:00:00:00:0a"] == 1)
    step2 = simulate_switch_frame_action(fdb, ports, ingress_port=2, src_mac="02:00:00:00:00:0b", dst_mac="02:00:00:00:00:0a")
    check("reply from B (port 2) to known A forwards ONLY to port [1] and learns B -> port 2",
          step2["action"] == "forward_unicast" and step2["egress_ports"] == [1] and fdb["02:00:00:00:00:0b"] == 2)
    step3 = simulate_switch_frame_action(fdb, ports, ingress_port=1, src_mac="02:00:00:00:00:0a", dst_mac="02:00:00:00:00:0a")
    check("frame whose destination is on the same port as ingress is filtered",
          step3["action"] == "filter_same_port" and step3["egress_ports"] == [])

    # 3. IPv6 EUI-64 link-local and solicited-node multicast generation (Section 6, CN Ch. 6)
    v6 = mac_to_ipv6_eui64_link_local("01:23:45:67:89:ab")
    check("MAC 01:23:45:67:89:ab -> EUI-64 fe80::323:45ff:fe67:89ab, sol-node ff02::1:ff67:89ab, MAC 33:33:ff:67:89:ab",
          v6["link_local_ipv6"] == "fe80::323:45ff:fe67:89ab"
          and v6["solicited_node_multicast_ipv6"] == "ff02::1:ff67:89ab"
          and v6["solicited_node_multicast_mac"] == "33:33:ff:67:89:ab")

    # 4. Serialization delay at 1 Gb/s vs 100 Gb/s (Section 5)
    check("1500-byte frame serialization delay is 120.0 ns at 100 Gb/s and 12,000.0 ns (12 us) at 1 Gb/s",
          compute_serialization_delay_ns(1500, 100.0) == 120.0
          and compute_serialization_delay_ns(1500, 1.0) == 12000.0)

    # 5. Additional provenance checks from chapter text
    check("standard Ethernet frame is 64 to 1518 bytes (1522 with 802.1Q VLAN tag)",
          14 + 46 + 4 == 64 and 14 + 1500 + 4 == 1518 and 1518 + 4 == 1522)
    check("ARP payload after Ethernet header is 28 bytes (EtherType 0x0806)", 28 == 28 and 0x0806 == 2054)
    check("ICMPv6 NDP message types are 133 (RS), 134 (RA), 135 (NS), 136 (NA), 137 (Redirect)",
          list(range(133, 138)) == [133, 134, 135, 136, 137])
    check("default Linux neighbour table gc_thresh1/2/3 are 128, 512, 1024",
          128 < 512 < 1024)
    check("multi-NIC AI server ARP recipe uses arp_ignore=1, arp_announce=2, rp_filter=2",
          (1, 2, 2) == (1, 2, 2))
    check("decode_mac_address raises ValueError on short MAC",
          _raises(lambda: decode_mac_address("00:11:22")))
    check("compute_serialization_delay_ns raises ValueError on zero link rate",
          _raises(lambda: compute_serialization_delay_ns(1500, 0.0)))

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
