# test_rows.py
def wrap(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

rows = [
    ("Three duplicate ACKs", "fast retransmit; SACK blocks show which ranges arrived"),
    ("Zero window", "the receiving application is slow to read"),
    ("Window full", "the sender is limited by the receive window"),
    ("Bytes in flight below cwnd", "the application itself is the limit"),
    ("Delayed ACK gap of 40 ms", "often the Nagle algorithm"),
    ("RTO gap of 200 ms or more, doubling on each retry", "retransmission timeout"),
    ("Segments larger than path MTU with DF set, then ICMP type 3 code 4", "path MTU problem"),
    ("Large packets retransmitted again and again with no ICMP reply", "black hole"),
    ("RST with a different TTL, IP ID or timing from the peer", "probably injected by a middlebox"),
    ("RST after a long idle period", "a NAT or load balancer timeout"),
    ("RST after data", "an application that closed with unread data"),
    ("Bad checksum on the sending host", "usually offload at work; a real fault only if the receiving side sees it too"),
]

# Total width = 1520 (from 40 to 1560)
# Suppose Col 1 width = 680, Col 2 width = 760, Arrow gap = 80
# Or table structure: Col 1 width = 690, arrow in between = 60, Col 2 width = 770 (690+60+770 = 1520)
# Inside Col 1: width 690. Padding 20 each side -> text width = 650.
# At 14.4 px/char (24px sans): 650 / 14.4 = 45.1 chars max.
# Inside Col 2: width 770. Padding 20 each side -> text width = 730.
# At 14.4 px/char: 730 / 14.4 = 50.6 chars max.

print("--- With Col 1 max_chars=45, Col 2 max_chars=50 ---")
for i, (c1, c2) in enumerate(rows, 1):
    l1 = wrap(c1, 45)
    l2 = wrap(c2, 50)
    print(f"Row {i:2d}: c1={len(l1)} lines, c2={len(l2)} lines -> max={max(len(l1), len(l2))}")
    for line in l1:
        if len(line) > 45: print(f"  OVERFLOW C1: {line}")
    for line in l2:
        if len(line) > 50: print(f"  OVERFLOW C2: {line}")
