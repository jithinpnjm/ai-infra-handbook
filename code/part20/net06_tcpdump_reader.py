#!/usr/bin/env python3
"""Read `tcpdump -nn` text lines: find retransmitted data and unanswered SYNs.
A retransmit here means the same flow sent the same seq range twice.
Line shape (Systems Performance ch 10):
  01:20:46.769073 IP 10.2.203.2.22 > 10.2.0.2.33771: Flags [P.], seq 1:193, ack 5, win 132, length 192"""
import re, sys

LINE = re.compile(r"IP (\S+) > (\S+?): Flags \[([^\]]+)\](?:, seq (\d+)(?::(\d+))?)?.*length (\d+)")

def parse(text):
    out = []
    for ln in text.splitlines():
        m = LINE.search(ln)
        if m:
            src, dst, flags, s1, s2, ln_ = m.groups()
            out.append({"src": src, "dst": dst, "flags": flags,
                        "seq": int(s1) if s1 else None, "len": int(ln_)})
    return out

def retransmits(pkts):
    seen, dup = set(), []
    for p in pkts:
        if p["len"] > 0 and p["seq"] is not None:
            key = (p["src"], p["dst"], p["seq"], p["len"])
            if key in seen:
                dup.append(key)
            seen.add(key)
    return dup

def unanswered_syns(pkts):
    """SYN (flags exactly 'S') whose reverse flow never shows 'S.'"""
    answered = {(p["dst"], p["src"]) for p in pkts if p["flags"] == "S."}
    syns = [p for p in pkts if p["flags"] == "S"]
    return [(p["src"], p["dst"]) for p in syns if (p["src"], p["dst"]) not in answered]

if __name__ == "__main__":
    pk = parse(sys.stdin.read())
    print("retransmits:", retransmits(pk))
    print("unanswered SYN:", unanswered_syns(pk))
