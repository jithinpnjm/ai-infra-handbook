col_widths = [450, 530, 520]
avail_widths = [w - 36 for w in col_widths] # 18px padding on each side!

splits = [
    # Row 1
    (["SYN at the server,", "no SYN-ACK back"],
     ["server firewall or a", "full listen queue"],
     ["firewall counters,", "nstat ListenOverflows, solisten"]),
    # Row 2
    (["SYN-ACK at the server", "but not at the client"],
     ["return path, asymmetric", "route or NAT"],
     ["conntrack, route check"]),
    # Row 3
    (["Data with repeated", "retransmissions and no ICMP"],
     ["MTU black hole or a", "stateful device that drops"],
     ["path MTU, firewall counters"]),
    # Row 4
    (["Duplicate ACKs and SACK"],
     ["loss on the path"],
     ["ss -ti, tcpretrans"]),
    # Row 5
    (["RST from a different TTL"],
     ["a middlebox"],
     ["compare TTL against normal peer packets"]),
    # Row 6
    (["Long idle then reset"],
     ["a timeout"],
     ["conntrack and NAT timers"]),
    # Row 7
    (["Gaps of exactly 200 ms or 1 s"],
     ["RTO or delayed ACK"],
     ["tcpstates, ss -ti"]),
    # Row 8
    (["DNS answers after 5 s"],
     ["resolver timeout"],
     ["repeat the query"]),
    # Row 9
    (["ClientHello then nothing"],
     ["TLS interception or an MTU problem;", "post-quantum key shares make", "ClientHellos large"],
     ["check path MTU"]),
    # Row 10
    (["Pause frames at multi-kHz", "rates on one priority"],
     ["a PFC storm"],
     ["switch counters per priority"]),
    # Row 11
    (["ECN-marked packets arrive", "but no CNP comes back"],
     ["NIC DCQCN probably misconfigured"],
     ["NIC settings"]),
]

rows = [
    ("SYN at the server, no SYN-ACK back", "server firewall or a full listen queue", "firewall counters, nstat ListenOverflows, solisten"),
    ("SYN-ACK at the server but not at the client", "return path, asymmetric route or NAT", "conntrack, route check"),
    ("Data with repeated retransmissions and no ICMP", "MTU black hole or a stateful device that drops", "path MTU, firewall counters"),
    ("Duplicate ACKs and SACK", "loss on the path", "ss -ti, tcpretrans"),
    ("RST from a different TTL", "a middlebox", "compare TTL against normal peer packets"),
    ("Long idle then reset", "a timeout", "conntrack and NAT timers"),
    ("Gaps of exactly 200 ms or 1 s", "RTO or delayed ACK", "tcpstates, ss -ti"),
    ("DNS answers after 5 s", "resolver timeout", "repeat the query"),
    ("ClientHello then nothing", "TLS interception or an MTU problem; post-quantum key shares make ClientHellos large", "check path MTU"),
    ("Pause frames at multi-kHz rates on one priority", "a PFC storm", "switch counters per priority"),
    ("ECN-marked packets arrive but no CNP comes back", "NIC DCQCN probably misconfigured", "NIC settings"),
]

all_ok = True
line_counts = []
for r_idx, row in enumerate(splits):
    orig = rows[r_idx]
    counts = []
    for c_idx, lines in enumerate(row):
        counts.append(len(lines))
        recombined = " ".join(lines)
        if recombined != orig[c_idx]:
            print(f"MISMATCH in Row {r_idx+1} Col {c_idx+1}: '{recombined}' vs '{orig[c_idx]}'")
            all_ok = False
        avail = avail_widths[c_idx]
        for line in lines:
            # Col 1: sans (0.60)
            # Col 2: sans (0.60)
            # Col 3: mono (0.62) or sans (0.60) - test with 0.62 for commands, 0.60 for plain
            rate = 14.88 if c_idx == 2 else 14.4
            w = len(line) * rate
            if w > avail:
                print(f"OVERFLOW in Row {r_idx+1} Col {c_idx+1}: '{line}' w={w:.1f} > avail={avail}")
                all_ok = False
    line_counts.append(max(counts))

if all_ok:
    print("ALL SPLITS PASSED PERFECTLY!")
    print("Line counts per row:", line_counts)
