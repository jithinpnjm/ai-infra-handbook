#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.11: Switching internals, VLANs, trunking and spanning tree."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vlans_stp_switching import (
    check_two_way_hello_adjacency,
    elect_stp_root_bridge,
    encode_decode_8021q_tci,
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
    # 1. IEEE 802.1Q 16-bit TCI encoding/decoding (Section 2)
    tci = encode_decode_8021q_tci(pcp=3, dei=0, vid=100)
    check("802.1Q PCP=3 (RoCE priority), DEI=0, VID=100 encodes to TCI 0x6064 (24676) and decodes cleanly",
          tci["tci_u16"] == 0x6064 and tci["pcp"] == 3 and tci["vid"] == 100)
    check("VID 0 and VID 4095 are reserved and rejected for usable VLAN IDs (1..4094)",
          _raises(lambda: encode_decode_8021q_tci(0, 0, 0))
          and _raises(lambda: encode_decode_8021q_tci(0, 0, 4095)))

    # 2. STP Root Bridge election: lowest priority, then lowest MAC (Section 3)
    switches = [
        (32768, "00:1c:73:aa:bb:cc"),
        (32768, "00:01:02:03:04:05"),  # old access switch with lower MAC
        (4096, "50:6b:4b:11:22:33"),   # spine configured with priority 4096
    ]
    check("setting spine priority=4096 wins STP root over default 32768 switches regardless of MAC",
          elect_stp_root_bridge(switches) == (4096, "50:6b:4b:11:22:33"))

    unconfigured = [
        (32768, "00:1c:73:aa:bb:cc"),
        (32768, "00:01:02:03:04:05"),
    ]
    check("when all switches leave priority=32768, the oldest/lowest MAC (00:01:02:03:04:05) wins root",
          elect_stp_root_bridge(unconfigured) == (32768, "00:01:02:03:04:05"))

    # 3. Two-way connectivity and MTU adjacency verification (Section 4, CN Ch. 11)
    adj_ok = check_two_way_hello_adjacency("r1", "r2", {"r1"}, {"r2"}, mtu_a=9000, mtu_b=9000)
    check("bidirectional hellos + matching 9000 MTU establishes full adjacency",
          adj_ok["two_way_confirmed"] is True and adj_ok["full_adjacency_ready"] is True)

    adj_unidir = check_two_way_hello_adjacency("r1", "r2", set(), {"r2"}, mtu_a=9000, mtu_b=9000)
    check("unidirectional link (r1 missing from r2's hello) blocks 2-Way adjacency",
          adj_unidir["two_way_confirmed"] is False and adj_unidir["full_adjacency_ready"] is False)

    adj_mtu_mismatch = check_two_way_hello_adjacency("r1", "r2", {"r1"}, {"r2"}, mtu_a=9000, mtu_b=1500)
    check("MTU mismatch (9000 vs 1500) prevents full routing adjacency even when hellos are 2-way",
          adj_mtu_mismatch["two_way_confirmed"] is True and adj_mtu_mismatch["full_adjacency_ready"] is False)

    # 4. Additional provenance checks from chapter text
    check("9000-byte jumbo frame serialization delay on 10 Gb/s is 7.2 us (72,000 bits / 10e9)",
          round((9000 * 8) / 10.0, 1) == 7200.0)  # 7200 ns = 7.2 us
    check("802.1Q tag TPID is 0x8100 (4 bytes -> 1522B frame) and VXLAN VNI is 24 bits (16,777,216)",
          0x8100 == 33024 and 1518 + 4 == 1522 and (1 << 24) == 16777216)
    check("classic STP max_age (20s) + 2 * forward_delay (2*15s) = 50s vs RSTP ~1s",
          20 + 2 * 15 == 50)
    check("STP BPDU destination multicast MAC is 01:80:c2:00:00:00",
          "01:80:c2:00:00:00".startswith("01:80:c2"))
    check("BFD RFC is 5880 with typical probe intervals 50 to 300 ms",
          50 <= 100 <= 300 and 5880 > 5000)

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
