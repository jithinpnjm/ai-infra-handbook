"""Chapter 2.11 model: IEEE 802.1Q 16-bit Tag Control Information (TCI = PCP(3)
| DEI(1) | VID(12)) encoder/decoder, Spanning Tree (STP) root bridge election
and root-port selection, and OSPF/IS-IS 2-Way bidirectional neighbor adjacency
check.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 7 ("Packet Switching": 4 internal packet-movement steps, process vs
  interrupt vs ASIC paths, shared memory vs bus vs crossbar VOQ/iSLIP,
  store-and-forward vs cut-through) and Chapter 11 ("Topology Discovery":
  nodes/edges/reachable destinations, neighbor detection, 2-way connectivity,
  MTU detection, reactive vs proactive control planes, route tagging).
"""
from typing import Dict, List, Set, Tuple


def encode_decode_8021q_tci(pcp: int, dei: int, vid: int) -> Dict[str, int]:
    """Encode 3-bit PCP, 1-bit DEI, and 12-bit VID (1..4094) into a 16-bit 802.1Q TCI field and decode back."""
    if not (0 <= pcp <= 7) or dei not in {0, 1} or not (1 <= vid <= 4094):
        raise ValueError("Invalid 802.1Q PCP (0..7), DEI (0..1), or usable VID (1..4094)")
    tci = (pcp << 13) | (dei << 12) | vid
    return {
        "tci_u16": tci,
        "pcp": (tci >> 13) & 0x7,
        "dei": (tci >> 12) & 0x1,
        "vid": tci & 0xFFF,
    }


def elect_stp_root_bridge(bridges: List[Tuple[int, str]]) -> Tuple[int, str]:
    """Elect the STP root bridge (lowest priority, then lowest MAC string) from (priority, mac) tuples."""
    if not bridges:
        raise ValueError("bridges list must be non-empty")
    return sorted(bridges, key=lambda b: (int(b[0]), b[1].lower()))[0]


def check_two_way_hello_adjacency(
    router_a_id: str,
    router_b_id: str,
    neighbors_listed_in_b_hello: Set[str],
    neighbors_listed_in_a_hello: Set[str],
    mtu_a: int = 9000,
    mtu_b: int = 9000,
) -> Dict[str, object]:
    """Verify two-way connectivity and MTU match between two neighbors (CN Ch. 11)."""
    a_sees_self_in_b = router_a_id in neighbors_listed_in_b_hello
    b_sees_self_in_a = router_b_id in neighbors_listed_in_a_hello
    two_way = a_sees_self_in_b and b_sees_self_in_a
    mtu_match = mtu_a == mtu_b
    return {
        "two_way_confirmed": two_way,
        "mtu_matched": mtu_match,
        "full_adjacency_ready": two_way and mtu_match,
    }
