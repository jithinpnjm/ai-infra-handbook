# Let's test all adjusted coordinates!

def check_pad(box_name, bx, by, bw, bh, text, fs, x, y, is_mono, anchor='start'):
    char_w = 0.62 * fs if is_mono else 0.6 * fs
    w = len(text) * char_w
    if anchor == 'middle':
        pad_l = (x - w/2) - bx
        pad_r = (bx + bw) - (x + w/2)
    else:
        pad_l = x - bx
        pad_r = (bx + bw) - (x + w)
    pad_t = y - 0.75 * fs - by
    pad_b = (by + bh) - (y + 0.25 * fs)
    ok = pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16
    print(f"[{'OK' if ok else 'FAIL'}] {box_name}: '{text[:30]}...' -> l={pad_l:.1f}, r={pad_r:.1f}, t={pad_t:.1f}, b={pad_b:.1f}")
    return ok

all_ok = True

# Title: (0, 0, 1600, 75)
all_ok &= check_pad("Title L1", 0, 0, 1600, 75, "The twelve lab steps, ", 48, 800, 36, False, 'middle')
all_ok &= check_pad("Title L2", 0, 0, 1600, 75, "from a healthy trace to the faults", 48, 800, 68, False, 'middle')

# Pre-step: (40, 80, 1520, 84)
all_ok &= check_pad("Pre-step L1", 40, 80, 1520, 84, "python3 code/part02/packet_capture_bpf_lab.py checks the byte-offset filters, ", 24, 128, 114, True)
all_ok &= check_pad("Pre-step L2", 40, 80, 1520, 84, "the 8.13 Mpps rate at 100 Gb/s, ring storage with -s 96, and the two-endpoint comparison", 24, 128, 142, True)

# Group 1 container: (40, 174, 1520, 246)
all_ok &= check_pad("G1 Header", 40, 174, 1520, 246, "Read a healthy trace", 30, 60, 206, False)

# Step 1 Card: (60, 224, 710, 180)
all_ok &= check_pad("S1 Title", 60, 224, 710, 180, "1 Handshake and teardown: ", 30, 202, 266, False)
all_ok &= check_pad("S1 Body L1", 60, 224, 710, 180, "curl to local nginx, label SYN, SYN-ACK, ", 24, 84, 308, True)
all_ok &= check_pad("S1 Body L2", 60, 224, 710, 180, "ACK, FIN, export with tshark -z follow", 24, 84, 342, True)

# Step 2 Card: (830, 224, 710, 180)
all_ok &= check_pad("S2 Title", 830, 224, 710, 180, "2 Filters: ", 30, 972, 266, False)
all_ok &= check_pad("S2 Body L1", 830, 224, 710, 180, "five capture filters for SYN only, RST, ", 24, 854, 298, False)
all_ok &= check_pad("S2 Body L2", 830, 224, 710, 180, "a port range, DSCP EF and VLAN, verified with ", 24, 854, 324, False)
all_ok &= check_pad("S2 Body L3", 830, 224, 710, 180, "tcpdump -d and hit counts, then the same ", 24, 854, 350, True)
all_ok &= check_pad("S2 Body L4", 830, 224, 710, 180, "logic as display filters", 24, 854, 376, False)

# Group 2 container: (40, 430, 740, 696)
all_ok &= check_pad("G2 Header", 40, 430, 740, 696, "Inject a fault and compare", 30, 60, 462, False)

# Steps 3..7 in G2: Card w = 700, h = 120. Gap = 14px.
# y positions:
# S3: 480
# S4: 614
# S5: 748
# S6: 882
# S7: 1016

# Check S3 (60, 480, 700, 120):
all_ok &= check_pad("S3 Title", 60, 480, 700, 120, "3 Retransmissions and loss: ", 30, 202, 520, False)
all_ok &= check_pad("S3 Body L1", 60, 480, 700, 120, "tc qdisc add dev veth1 root netem loss 2%, ", 24, 84, 554, True)
all_ok &= check_pad("S3 Body L2", 60, 480, 700, 120, "compare with 0% loss", 24, 84, 582, False)

# S4 (60, 614, 700, 120):
all_ok &= check_pad("S4 Title", 60, 614, 700, 120, "4 MTU black hole: ", 30, 202, 654, False)
all_ok &= check_pad("S4 Body L1", 60, 614, 700, 120, "smaller MTU on a router namespace, drop ICMP ", 24, 84, 688, False)
all_ok &= check_pad("S4 Body L2", 60, 614, 700, 120, "type 3 code 4, then fix with MSS clamping", 24, 84, 716, False)

# S5 (60, 748, 700, 120):
all_ok &= check_pad("S5 Title", 60, 748, 700, 120, "5 Zero window: ", 30, 202, 792, False)
all_ok &= check_pad("S5 Body", 60, 748, 700, 120, "a server that sleeps before it reads", 24, 84, 836, False)

# S6 (60, 882, 700, 120):
all_ok &= check_pad("S6 Title", 60, 882, 700, 120, "6 TLS: ", 30, 202, 922, False)
all_ok &= check_pad("S6 Body L1", 60, 882, 700, 120, "SSLKEYLOGFILE=/tmp/keys.log curl ", 24, 84, 956, True)
all_ok &= check_pad("S6 Body L2", 60, 882, 700, 120, "https://localhost, read SNI and ALPN", 24, 84, 984, True)

# S7 (60, 1016, 700, 120):
all_ok &= check_pad("S7 Title", 60, 1016, 700, 120, "7 Offload artefacts: ", 30, 202, 1060, False)
all_ok &= check_pad("S7 Body", 60, 1016, 700, 120, "TSO and checksum offload on then off", 24, 84, 1104, False)

# Group 3 container: (820, 430, 740, 696)
all_ok &= check_pad("G3 Header", 820, 430, 740, 696, "Wider tools", 30, 840, 462, False)

# S8 (840, 480, 700, 120):
all_ok &= check_pad("S8 Title", 840, 480, 700, 120, "8 Overlay: ", 30, 982, 524, False)
all_ok &= check_pad("S8 Body", 840, 480, 700, 120, "VXLAN link as in chapter 2.17, Decode As", 24, 864, 568, False)

# S9 (840, 614, 700, 120):
all_ok &= check_pad("S9 Title", 840, 614, 700, 120, "9 Ring buffer and trigger: ", 30, 982, 654, False)
all_ok &= check_pad("S9 Body", 840, 614, 700, 120, "tcpdump -C 10 -W 5 plus a stop script", 24, 864, 698, True)

# S10 (840, 748, 700, 120):
all_ok &= check_pad("S10 Title", 840, 748, 700, 120, "10 BPF tools: ", 30, 982, 788, False)
all_ok &= check_pad("S10 Body L1", 840, 748, 700, 120, "tcplife, tcpconnect, tcpretrans, tcpdrop, ", 24, 864, 822, True)
all_ok &= check_pad("S10 Body L2", 840, 748, 700, 120, "three bpftrace one-liners", 24, 864, 850, False)

# S11 (840, 882, 700, 120):
all_ok &= check_pad("S11 Title", 840, 882, 700, 120, "11 Container capture: ", 30, 982, 922, False)
all_ok &= check_pad("S11 Body L1", 840, 882, 700, 120, "nsenter, then docker run --network ", 24, 864, 956, True)
all_ok &= check_pad("S11 Body L2", 840, 882, 700, 120, "container:NAME nicolaka/netshoot tcpdump", 24, 864, 984, True)

# S12 (840, 1016, 700, 120):
all_ok &= check_pad("S12 Title L1", 840, 1016, 700, 120, "12 Clean up and delete captures, ", 26, 982, 1056, False)
all_ok &= check_pad("S12 Title L2", 840, 1016, 700, 120, "key log and ring-buffer directory", 26, 864, 1096, False)

# Bottom Bar: (40, 1136, 1520, 52)
all_ok &= check_pad("Bottom Bar", 40, 1136, 1520, 52, "The healthy trace from step 1 is the reference that makes the faulty traces stand out", 24, 800, 1168, False, 'middle')

print(f"\nOVERALL RESULT: {'ALL PASS!' if all_ok else 'SOME FAILED!'}")
