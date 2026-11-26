# Let's see if 3 columns can work with proper word wrapping!

avail_w = 400 # 450 card width - 50 padding

steps_raw = {
    1: ("1 Handshake and teardown:", "curl to local nginx, label SYN, SYN-ACK, ACK, FIN, export with tshark -z follow"),
    2: ("2 Filters:", "five capture filters for SYN only, RST, a port range, DSCP EF and VLAN, verified with tcpdump -d and hit counts, then the same logic as display filters"),
    3: ("3 Retransmissions and loss:", "tc qdisc add dev veth1 root netem loss 2%, compare with 0% loss"),
    4: ("4 MTU black hole:", "smaller MTU on a router namespace, drop ICMP type 3 code 4, then fix with MSS clamping"),
    5: ("5 Zero window:", "a server that sleeps before it reads"),
    6: ("6 TLS:", "SSLKEYLOGFILE=/tmp/keys.log curl https://localhost, read SNI and ALPN"),
    7: ("7 Offload artefacts:", "TSO and checksum offload on then off"),
    8: ("8 Overlay:", "VXLAN link as in chapter 2.17, Decode As"),
    9: ("9 Ring buffer and trigger:", "tcpdump -C 10 -W 5 plus a stop script"),
    10: ("10 BPF tools:", "tcplife, tcpconnect, tcpretrans, tcpdrop, three bpftrace one-liners"),
    11: ("11 Container capture:", "nsenter, then docker run --network container:NAME nicolaka/netshoot tcpdump"),
    12: ("12 Clean up and delete captures, key log and ring-buffer directory", ""),
}

def wrap_words(text, fs, is_mono=False):
    words = text.split()
    lines = []
    cur = []
    cur_w = 0
    for w in words:
        char_w = 0.62 * fs if (is_mono or any(c in w for c in ['/', '=', '-', '_', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])) else 0.6 * fs
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
    return lines

for num, (title, body) in steps_raw.items():
    t_lines = wrap_words(title, 30, False)
    b_lines = wrap_words(body, 24, False) if body else []
    total_lines = len(t_lines) + len(b_lines)
    print(f"Step {num}: {len(t_lines)} title lines + {len(b_lines)} body lines = {total_lines} total lines")
    for l in t_lines:
        w = len(l) * 18
        if w > avail_w: print(f"  OVERFLOW TITLE: '{l}' (w={w})")
    for l in b_lines:
        w = sum(14.88 if any(c in w for c in ['/', '=', '-', '_', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) else 14.4 for w in l)
        if w > avail_w: print(f"  OVERFLOW BODY: '{l}' (w={w})")
