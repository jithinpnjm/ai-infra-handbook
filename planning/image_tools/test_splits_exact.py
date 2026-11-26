# test_splits_exact.py

def wrap_words(text, max_len):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        added = len(w) if not curr else len(w) + 1
        if curr_len + added <= max_len:
            curr.append(w)
            curr_len += added
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

for i, (c1, c2) in enumerate(rows, 1):
    l1 = wrap_words(c1, 47)
    l2 = wrap_words(c2, 51)
    print(f"Row {i:2d}: C1 ({len(l1)} lines): {l1}")
    print(f"        C2 ({len(l2)} lines): {l2}")
    for line in l1:
        assert len(line) <= 47, f"C1 line too long: {line}"
    for line in l2:
        assert len(line) <= 51, f"C2 line too long: {line}"

print("\nALL LINES FIT IN WIDTH BUDGET!")
