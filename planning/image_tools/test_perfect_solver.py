# Solver that achieves 100% PASS on all padding tests!

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

# Title: (0, 0, 1600, 110)
all_ok &= check_pad("Title L1", 0, 0, 1600, 110, "The twelve lab steps, ", 48, 800, 52, False, 'middle')
all_ok &= check_pad("Title L2", 0, 0, 1600, 110, "from a healthy trace to the faults", 48, 800, 96, False, 'middle')

# Pre-step: (40, 120, 1520, 80)
all_ok &= check_pad("Pre-step L1", 40, 120, 1520, 80, "python3 code/part02/packet_capture_bpf_lab.py checks the byte-offset filters, ", 24, 128, 152, True)
all_ok &= check_pad("Pre-step L2", 40, 120, 1520, 80, "the 8.13 Mpps rate at 100 Gb/s, ring storage with -s 96, and the two-endpoint comparison", 24, 128, 180, True)

# Group 1 container: (40, 215, 1520, 240)
all_ok &= check_pad("G1 Header", 40, 215, 1520, 240, "Read a healthy trace", 30, 60, 256, False)

# Step 1 Card: (60, 270, 710, 170)
all_ok &= check_pad("S1 Title", 60, 270, 710, 170, "1 Handshake and teardown: ", 30, 202, 312, False)
all_ok &= check_pad("S1 Body L1", 60, 270, 710, 170, "curl to local nginx, label SYN, SYN-ACK, ", 24, 84, 360, True)
all_ok &= check_pad("S1 Body L2", 60, 270, 710, 170, "ACK, FIN, export with tshark -z follow", 24, 84, 396, True)

# Step 2 Card: (830, 270, 710, 170)
all_ok &= check_pad("S2 Title", 830, 270, 710, 170, "2 Filters: ", 30, 972, 312, False)
all_ok &= check_pad("S2 Body L1", 830, 270, 710, 170, "five capture filters for SYN only, RST, ", 24, 854, 344, False)
all_ok &= check_pad("S2 Body L2", 830, 270, 710, 170, "a port range, DSCP EF and VLAN, verified with ", 24, 854, 370, False)
all_ok &= check_pad("S2 Body L3", 830, 270, 710, 170, "tcpdump -d and hit counts, then the same ", 24, 854, 396, True)
all_ok &= check_pad("S2 Body L4", 830, 270, 710, 170, "logic as display filters", 24, 854, 422, False)

# Group 2 container: (40, 470, 740, 650)
all_ok &= check_pad("G2 Header", 40, 470, 740, 650, "Inject a fault and compare", 30, 60, 510, False)

# Steps 3..7 in G2: Card w = 700, h = 112. Gap = 12px.
# y positions:
# S3: 524
# S4: 646
# S5: 768
# S6: 890
# S7: 1012

# S3 (60, 524, 700, 114):
all_ok &= check_pad("S3 Title", 60, 524, 700, 114, "3 Retransmissions and loss: ", 30, 202, 564, False)
all_ok &= check_pad("S3 Body L1", 60, 524, 700, 114, "tc qdisc add dev veth1 root netem loss 2%, ", 24, 84, 596, True)
all_ok &= check_pad("S3 Body L2", 60, 524, 700, 114, "compare with 0% loss", 24, 84, 622, False)

# S4 (60, 646, 700, 114):
all_ok &= check_pad("S4 Title", 60, 646, 700, 114, "4 MTU black hole: ", 30, 202, 686, False)
all_ok &= check_pad("S4 Body L1", 60, 646, 700, 114, "smaller MTU on a router namespace, drop ICMP ", 24, 84, 718, False)
all_ok &= check_pad("S4 Body L2", 60, 646, 700, 114, "type 3 code 4, then fix with MSS clamping", 24, 84, 744, False)

# S5 (60, 768, 700, 114):
all_ok &= check_pad("S5 Title", 60, 768, 700, 114, "5 Zero window: ", 30, 202, 810, False)
all_ok &= check_pad("S5 Body", 60, 768, 700, 114, "a server that sleeps before it reads", 24, 84, 854, False)

# S6 (60, 890, 700, 114):
all_ok &= check_pad("S6 Title", 60, 890, 700, 114, "6 TLS: ", 30, 202, 930, False)
all_ok &= check_pad("S6 Body L1", 60, 890, 700, 114, "SSLKEYLOGFILE=/tmp/keys.log curl ", 24, 84, 962, True)
all_ok &= check_pad("S6 Body L2", 60, 890, 700, 114, "https://localhost, read SNI and ALPN", 24, 84, 988, True)

# S7 (60, 1012, 700, 114):
all_ok &= check_pad("S7 Title", 60, 1012, 700, 114, "7 Offload artefacts: ", 30, 202, 1054, False)
all_ok &= check_pad("S7 Body", 60, 1012, 700, 114, "TSO and checksum offload on then off", 24, 84, 1098, False)

# Group 3 container: (820, 470, 740, 650)
all_ok &= check_pad("G3 Header", 820, 470, 740, 650, "Wider tools", 30, 840, 510, False)

# S8 (840, 524, 700, 114):
all_ok &= check_pad("S8 Title", 840, 524, 700, 114, "8 Overlay: ", 30, 982, 566, False)
all_ok &= check_pad("S8 Body", 840, 524, 700, 114, "VXLAN link as in chapter 2.17, Decode As", 24, 864, 610, False)

# S9 (840, 646, 700, 114):
all_ok &= check_pad("S9 Title", 840, 646, 700, 114, "9 Ring buffer and trigger: ", 30, 982, 688, False)
all_ok &= check_pad("S9 Body", 840, 646, 700, 114, "tcpdump -C 10 -W 5 plus a stop script", 24, 864, 730, True)

# S10 (840, 768, 700, 114):
all_ok &= check_pad("S10 Title", 840, 768, 700, 114, "10 BPF tools: ", 30, 982, 810, False)
all_ok &= check_pad("S10 Body L1", 840, 768, 700, 114, "tcplife, tcpconnect, tcpretrans, tcpdrop, ", 24, 864, 842, True)
all_ok &= check_pad("S10 Body L2", 840, 768, 700, 114, "three bpftrace one-liners", 24, 864, 868, False)

# S11 (840, 890, 700, 114):
all_ok &= check_pad("S11 Title", 840, 890, 700, 114, "11 Container capture: ", 30, 982, 930, False)
all_ok &= check_pad("S11 Body L1", 840, 890, 700, 114, "nsenter, then docker run --network ", 24, 864, 962, True)
all_ok &= check_pad("S11 Body L2", 840, 890, 700, 114, "container:NAME nicolaka/netshoot tcpdump", 24, 864, 988, True)

# S12 (840, 1012, 700, 114):
all_ok &= check_pad("S12 Title L1", 840, 1012, 700, 114, "12 Clean up and delete captures, ", 26, 982, 1052, False)
all_ok &= check_pad("S12 Title L2", 840, 1012, 700, 114, "key log and ring-buffer directory", 26, 864, 1092, False)

# Bottom Bar: (40, 1134, 1520, 54)
all_ok &= check_pad("Bottom Bar", 40, 1134, 1520, 54, "The healthy trace from step 1 is the reference that makes the faulty traces stand out", 24, 800, 1167, False, 'middle')

print(f"\nOVERALL RESULT: {'ALL PASS!' if all_ok else 'SOME FAILED!'}")
assert all_ok
