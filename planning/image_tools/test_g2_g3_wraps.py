steps_g2_g3 = [
    (3, "3 Retransmissions and loss: tc qdisc add dev veth1 root netem loss 2%, compare with 0% loss"),
    (4, "4 MTU black hole: smaller MTU on a router namespace, drop ICMP type 3 code 4, then fix with MSS clamping"),
    (5, "5 Zero window: a server that sleeps before it reads"),
    (6, "6 TLS: SSLKEYLOGFILE=/tmp/keys.log curl https://localhost, read SNI and ALPN"),
    (7, "7 Offload artefacts: TSO and checksum offload on then off"),
    (8, "8 Overlay: VXLAN link as in chapter 2.17, Decode As"),
    (9, "9 Ring buffer and trigger: tcpdump -C 10 -W 5 plus a stop script"),
    (10, "10 BPF tools: tcplife, tcpconnect, tcpretrans, tcpdrop, three bpftrace one-liners"),
    (11, "11 Container capture: nsenter, then docker run --network container:NAME nicolaka/netshoot tcpdump"),
    (12, "12 Clean up and delete captures, key log and ring-buffer directory"),
]

# In 700px card, available text width for body (spans across the card):
# If text is left aligned at x = card_x + 24:
# available width = 700 - 48 = 652px.
avail_w = 652

for num, s in steps_g2_g3:
    if ":" in s:
        title, body = s.split(":", 1)
        title += ":"
        body = body.strip()
    else:
        title = s
        body = ""
    print(f"\nStep {num}:")
    print(f"  Title: '{title}' (chars={len(title)}, w={len(title)*18:.1f} vs {avail_w})")
    
    # Body wrap
    words = body.split()
    lines = []
    cur = []
    cur_w = 0
    for w in words:
        char_w = 14.88 if any(c in w for c in ['/', '=', '-', '_', '0', '1', '2']) else 14.4
        ww = len(w) * char_w + (char_w if cur else 0)
        if cur_w + ww <= avail_w:
            cur.append(w)
            cur_w += ww
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
            cur_w = len(w) * char_w
    if cur:
        lines.append(" ".join(cur))
        
    print(f"  Body lines ({len(lines)}):")
    for i, l in enumerate(lines):
        lw = sum(14.88 if any(c in w for c in ['/', '=', '-', '_', '0', '1', '2']) else 14.4 for w in l)
        print(f"    Line {i+1}: '{l}' (w={lw:.1f}, pad={avail_w - lw:.1f})")
