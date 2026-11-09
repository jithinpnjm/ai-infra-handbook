#!/usr/bin/env python3
"""MTU, MSS and ping-size arithmetic for black-hole debugging.
Header sizes: IPv4 20, TCP 20 (no options), ICMP 8. VXLAN adds 50 bytes
(handbook 2.17). ping -s sets only the ICMP payload."""
IP, TCP, ICMP = 20, 20, 8

def inner_mtu(link_mtu, overhead=0):
    return link_mtu - overhead

def tcp_mss(mtu):
    return mtu - IP - TCP

def ping_payload_for(mtu):
    """Largest `ping -M do -s N` that fits without fragmenting."""
    return mtu - IP - ICMP

def blackhole_risk(path_mtu, sender_mtu, icmp_frag_needed_arrives):
    """A DF packet that is too big is dropped. Only the ICMP message lets
    the sender shrink. If ICMP is filtered, small packets pass, big ones hang."""
    if sender_mtu <= path_mtu:
        return "fits"
    return "shrinks via PMTUD" if icmp_frag_needed_arrives else "BLACK HOLE"

if __name__ == "__main__":
    for mtu in (1500, 1450, 9000):
        print(mtu, "mss", tcp_mss(mtu), "ping -s", ping_payload_for(mtu))
