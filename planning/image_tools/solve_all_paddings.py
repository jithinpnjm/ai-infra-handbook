# Complete padding solver for all cards in the layout

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

# Title: (0, 0, 1600, 60)
all_ok &= check_pad("Title", 0, 0, 1600, 60, "The twelve lab steps, from a healthy trace to the faults", 48, 800, 48, False, 'middle')

# Pre-step: (40, 64, 1520, 84)
all_ok &= check_pad("Pre-step L1", 40, 64, 1520, 84, "python3 code/part02/packet_capture_bpf_lab.py checks the byte-offset filters, ", 24, 128, 98, True)
all_ok &= check_pad("Pre-step L2", 40, 64, 1520, 84, "the 8.13 Mpps rate at 100 Gb/s, ring storage with -s 96, and the two-endpoint comparison", 24, 128, 124, True)

# Group 1 container: (40, 158, 1520, 230)
all_ok &= check_pad("G1 Header", 40, 158, 1520, 230, "Read a healthy trace", 30, 60, 186, False)

# Step 1 Card: (60, 204, 710, 168)
all_ok &= check_pad("S1 Title", 60, 204, 710, 168, "1 Handshake and teardown: ", 30, 202, 246, False)
all_ok &= check_pad("S1 Body L1", 60, 204, 710, 168, "curl to local nginx, label SYN, SYN-ACK, ", 24, 84, 288, True)
all_ok &= check_pad("S1 Body L2", 60, 204, 710, 168, "ACK, FIN, export with tshark -z follow", 24, 84, 318, True)

# Step 2 Card: (830, 204, 710, 168)
all_ok &= check_pad("S2 Title", 830, 204, 710, 168, "2 Filters: ", 30, 972, 246, False)
all_ok &= check_pad("S2 Body L1", 830, 204, 710, 168, "five capture filters for SYN only, RST, ", 24, 854, 276, False)
all_ok &= check_pad("S2 Body L2", 830, 204, 710, 168, "a port range, DSCP EF and VLAN, verified with ", 24, 854, 302, False)
all_ok &= check_pad("S2 Body L3", 830, 204, 710, 168, "tcpdump -d and hit counts, then the same ", 24, 854, 328, True)
all_ok &= check_pad("S2 Body L4", 830, 204, 710, 168, "logic as display filters", 24, 854, 354, False)

# Group 2 container: (40, 398, 740, 728)
all_ok &= check_pad("G2 Header", 40, 398, 740, 728, "Inject a fault and compare", 30, 60, 428, False)

# Steps 3..7 in G2: Card w = 700, h = 124.
# Gaps = 18px.
# y positions:
# S3: 446
# S4: 588
# S5: 730
# S6: 872
# S7: 1014
# Check S3 (60, 446, 700, 124):
all_ok &= check_pad("S3 Title", 60, 446, 700, 124, "3 Retransmissions and loss: ", 30, 202, 482, False)
all_ok &= check_pad("S3 Body L1", 60, 446, 700, 124, "tc qdisc add dev veth1 root netem loss 2%, ", 24, 84, 518, True)
all_ok &= check_pad("S3 Body L2", 60, 446, 700, 124, "compare with 0% loss", 24, 84, 546, False)

# S4 (60, 588, 700, 124):
all_ok &= check_pad("S4 Title", 60, 588, 700, 124, "4 MTU black hole: ", 30, 202, 624, False)
all_ok &= check_pad("S4 Body L1", 60, 588, 700, 124, "smaller MTU on a router namespace, drop ICMP ", 24, 84, 660, False)
all_ok &= check_pad("S4 Body L2", 60, 588, 700, 124, "type 3 code 4, then fix with MSS clamping", 24, 84, 688, False)

# S5 (60, 730, 700, 124):
all_ok &= check_pad("S5 Title", 60, 730, 700, 124, "5 Zero window: ", 30, 202, 770, False)
all_ok &= check_pad("S5 Body", 60, 730, 700, 124, "a server that sleeps before it reads", 24, 84, 814, False)

# S6 (60, 872, 700, 124):
all_ok &= check_pad("S6 Title", 60, 872, 700, 124, "6 TLS: ", 30, 202, 908, False)
all_ok &= check_pad("S6 Body L1", 60, 872, 700, 124, "SSLKEYLOGFILE=/tmp/keys.log curl ", 24, 84, 944, True)
all_ok &= check_pad("S6 Body L2", 60, 872, 700, 124, "https://localhost, read SNI and ALPN", 24, 84, 972, True)

# S7 (60, 1014, 700, 124):
all_ok &= check_pad("S7 Title", 60, 1014, 700, 124, "7 Offload artefacts: ", 30, 202, 1054, False)
all_ok &= check_pad("S7 Body", 60, 1014, 700, 124, "TSO and checksum offload on then off", 24, 84, 1098, False)

# Group 3 container: (820, 398, 740, 728)
all_ok &= check_pad("G3 Header", 820, 398, 740, 728, "Wider tools", 30, 840, 428, False)

# S8 (840, 446, 700, 124):
all_ok &= check_pad("S8 Title", 840, 446, 700, 124, "8 Overlay: ", 30, 982, 486, False)
all_ok &= check_pad("S8 Body", 840, 446, 700, 124, "VXLAN link as in chapter 2.17, Decode As", 24, 864, 530, False)

# S9 (840, 588, 700, 124):
all_ok &= check_pad("S9 Title", 840, 588, 700, 124, "9 Ring buffer and trigger: ", 30, 982, 626, False)
all_ok &= check_pad("S9 Body", 840, 588, 700, 124, "tcpdump -C 10 -W 5 plus a stop script", 24, 864, 670, True)

# S10 (840, 730, 700, 124):
all_ok &= check_pad("S10 Title", 840, 730, 700, 124, "10 BPF tools: ", 30, 982, 766, False)
all_ok &= check_pad("S10 Body L1", 840, 730, 700, 124, "tcplife, tcpconnect, tcpretrans, tcpdrop, ", 24, 864, 802, True)
all_ok &= check_pad("S10 Body L2", 840, 730, 700, 124, "three bpftrace one-liners", 24, 864, 830, False)

# S11 (840, 872, 700, 124):
all_ok &= check_pad("S11 Title", 840, 872, 700, 124, "11 Container capture: ", 30, 982, 908, False)
all_ok &= check_pad("S11 Body L1", 840, 872, 700, 124, "nsenter, then docker run --network ", 24, 864, 944, True)
all_ok &= check_pad("S11 Body L2", 840, 872, 700, 124, "container:NAME nicolaka/netshoot tcpdump", 24, 864, 972, True)

# S12 (840, 1014, 700, 124):
all_ok &= check_pad("S12 Title L1", 840, 1014, 700, 124, "12 Clean up and delete captures, ", 26, 982, 1052, False)
all_ok &= check_pad("S12 Title L2", 840, 1014, 700, 124, "key log and ring-buffer directory", 26, 864, 1092, False)

# Bottom Bar: (40, 1138, 1520, 46)
all_ok &= check_pad("Bottom Bar", 40, 1138, 1520, 46, "The healthy trace from step 1 is the reference that makes the faulty traces stand out", 24, 800, 1168, False, 'middle')

print(f"\nOVERALL RESULT: {'ALL PASS!' if all_ok else 'SOME FAILED!'}")
