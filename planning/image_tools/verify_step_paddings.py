# Test script to verify all text lines in 3 columns against strict padding >= 16px

# Col 1: Group 1 (steps 1, 2)
# Col 2: Group 2 (steps 3, 4, 5, 6, 7)
# Col 3: Group 3 (steps 8, 9, 10, 11, 12)

# Card width in all columns: 450px (x_pad = 15 inside 480 container)
# Box bounds: bw = 450, bh = 154 (or 160)

box_w = 450

step_lines = {
    1: [
        ("1 Handshake and teardown:", 30, False),
        ("curl to local nginx,", 24, True),
        ("label SYN, SYN-ACK, ACK, FIN,", 24, False),
        ("export with tshark -z follow", 24, True),
    ],
    2: [
        ("2 Filters:", 30, False),
        ("five capture filters for SYN only,", 24, False),
        ("RST, a port range, DSCP EF and VLAN,", 24, False),
        ("verified with tcpdump -d and hit counts,", 24, True),
        ("then the same logic as display filters", 24, False),
    ],
    3: [
        ("3 Retransmissions", 30, False),
        ("and loss:", 30, False),
        ("tc qdisc add dev veth1 root", 24, True),
        ("netem loss 2%, compare", 24, True),
        ("with 0% loss", 24, False),
    ],
    4: [
        ("4 MTU black hole:", 30, False),
        ("smaller MTU on a router", 24, False),
        ("namespace, drop ICMP type 3", 24, False),
        ("code 4, then fix with MSS clamping", 24, False),
    ],
    5: [
        ("5 Zero window:", 30, False),
        ("a server that sleeps", 24, False),
        ("before it reads", 24, False),
    ],
    6: [
        ("6 TLS:", 30, False),
        ("SSLKEYLOGFILE=/tmp/keys.log", 24, True),
        ("curl https://localhost,", 24, True),
        ("read SNI and ALPN", 24, False),
    ],
    7: [
        ("7 Offload artefacts:", 30, False),
        ("TSO and checksum offload", 24, False),
        ("on then off", 24, False),
    ],
    8: [
        ("8 Overlay:", 30, False),
        ("VXLAN link as in chapter 2.17,", 24, False),
        ("Decode As", 24, False),
    ],
    9: [
        ("9 Ring buffer and trigger:", 30, False),
        ("tcpdump -C 10 -W 5", 24, True),
        ("plus a stop script", 24, False),
    ],
    10: [
        ("10 BPF tools:", 30, False),
        ("tcplife, tcpconnect, tcpretrans,", 24, True),
        ("tcpdrop, three bpftrace", 24, True),
        ("one-liners", 24, False),
    ],
    11: [
        ("11 Container capture:", 30, False),
        ("nsenter, then docker run", 24, True),
        ("--network container:NAME", 24, True),
        ("nicolaka/netshoot tcpdump", 24, True),
    ],
    12: [
        ("12 Clean up and delete", 30, False),
        ("captures, key log and", 30, False),
        ("ring-buffer directory", 30, False),
    ]
}

# Verify horizontal padding for each line:
all_ok = True
for num, lines in step_lines.items():
    print(f"\n--- Step {num} ---")
    for text, fs, is_mono in lines:
        char_w = 0.62 * fs if is_mono else 0.6 * fs
        w = len(text) * char_w
        pad = (box_w - w) / 2 # if centered
        print(f"  '{text}' (fs={fs}, mono={is_mono}): len={len(text)}, w={w:.1f}, pad_center={pad:.1f}, pad_left20={box_w - w - 20:.1f}")
        if (box_w - w - 20) < 16:
            print(f"  ERROR: padding < 16 on '{text}'!")
            all_ok = False

if all_ok:
    print("\nALL LINES SATISFY >= 16px PADDING CHECK!")
