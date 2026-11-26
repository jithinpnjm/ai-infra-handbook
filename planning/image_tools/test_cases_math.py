cases = [
    # Case a
    ("Case a - Left", [
        ("a: SYN at the client and", 24),
        ("at the server, no SYN-ACK", 24)
    ]),
    ("Case a - Right", [
        ("server firewall or a full listen queue", 24)
    ]),
    
    # Case b
    ("Case b - Left", [
        ("b: SYN-ACK leaves the server", 24),
        ("but never reaches the client", 24)
    ]),
    ("Case b - Right", [
        ("return path, asymmetric route or NAT", 24)
    ]),

    # Case c
    ("Case c - Left", [
        ("c: RST reaches the client with a TTL", 24),
        ("different from the server's normal packets", 24)
    ]),
    ("Case c - Right", [
        ("a middlebox injected it", 24)
    ]),

    # Case d
    ("Case d - Left", [
        ("d: SYN-ACK with no wscale option", 24)
    ]),
    ("Case d - Right", [
        ("a middlebox stripping options;", 24),
        ("throughput limited to 64 KB per RTT", 24)
    ]),

    # Case e
    ("Case e - Left", [
        ("e: full-size segments retransmitted", 24),
        ("repeatedly, no ICMP 3/4 replies", 24)
    ]),
    ("Case e - Right", [
        ("MTU black hole or a stateful device", 24),
        ("dropping the packets", 24)
    ])
]

bw = 720
for name, lines in cases:
    print(f"=== {name} ===")
    for txt, fs in lines:
        w = len(txt) * 0.6 * fs
        rem = bw - w
        pad = rem / 2 # if centered, or rem - 30 if start
        print(f"  '{txt}' ({len(txt)}c, {w:.1f}px) -> rem={rem:.1f}px, if left=30, pad_r={rem-30:.1f}px")
        assert rem - 30 >= 16, f"Padding violation: {rem-30} < 16"
