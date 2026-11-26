# Simulation of 2-column layout

box_w = 700

step_lines_2col = {
    1: [
        ("1 Handshake and teardown:", 30, False),
        ("curl to local nginx, label SYN, SYN-ACK,", 24, True),
        ("ACK, FIN, export with tshark -z follow", 24, True),
    ],
    2: [
        ("2 Filters:", 30, False),
        ("five capture filters for SYN only, RST,", 24, False),
        ("a port range, DSCP EF and VLAN, verified with", 24, False),
        ("tcpdump -d and hit counts, then the same", 24, True),
        ("logic as display filters", 24, False),
    ],
    3: [
        ("3 Retransmissions and loss:", 30, False),
        ("tc qdisc add dev veth1 root netem loss 2%,", 24, True),
        ("compare with 0% loss", 24, False),
    ],
    4: [
        ("4 MTU black hole:", 30, False),
        ("smaller MTU on a router namespace, drop ICMP", 24, False),
        ("type 3 code 4, then fix with MSS clamping", 24, False),
    ],
    5: [
        ("5 Zero window:", 30, False),
        ("a server that sleeps before it reads", 24, False),
    ],
    6: [
        ("6 TLS:", 30, False),
        ("SSLKEYLOGFILE=/tmp/keys.log curl", 24, True),
        ("https://localhost, read SNI and ALPN", 24, True),
    ],
    7: [
        ("7 Offload artefacts:", 30, False),
        ("TSO and checksum offload on then off", 24, False),
    ],
    8: [
        ("8 Overlay:", 30, False),
        ("VXLAN link as in chapter 2.17, Decode As", 24, False),
    ],
    9: [
        ("9 Ring buffer and trigger:", 30, False),
        ("tcpdump -C 10 -W 5 plus a stop script", 24, True),
    ],
    10: [
        ("10 BPF tools:", 30, False),
        ("tcplife, tcpconnect, tcpretrans, tcpdrop,", 24, True),
        ("three bpftrace one-liners", 24, True),
    ],
    11: [
        ("11 Container capture:", 30, False),
        ("nsenter, then docker run --network", 24, True),
        ("container:NAME nicolaka/netshoot tcpdump", 24, True),
    ],
    12: [
        ("12 Clean up and delete captures,", 30, False),
        ("key log and ring-buffer directory", 30, False),
    ]
}

print("Checking 2-column layout (box_w = 700):")
all_ok = True
for num, lines in step_lines_2col.items():
    print(f"\n--- Step {num} ({len(lines)} lines) ---")
    for text, fs, is_mono in lines:
        char_w = 0.62 * fs if is_mono else 0.6 * fs
        w = len(text) * char_w
        pad_center = (box_w - w) / 2
        pad_left24 = box_w - w - 24
        print(f"  '{text}' (fs={fs}, mono={is_mono}): len={len(text)}, w={w:.1f}, pad_left24={pad_left24:.1f}")
        if pad_left24 < 16:
            print(f"  ERROR: pad_left24 < 16 on '{text}'!")
            all_ok = False

if all_ok:
    print("\nALL LINES SATISFY >= 16px HORIZONTAL PADDING IN 2-COLUMN LAYOUT!")
