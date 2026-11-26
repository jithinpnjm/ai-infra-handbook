labels_right = [
    ("capture on the server interface", ["capture on the server interface"]),
    ("capture on the client interface; the offload caveat still applies", 
     ["capture on the client interface;", "the offload caveat still applies"]),
    ("nsenter -t PID -n tcpdump", ["nsenter -t PID -n tcpdump"]),
    ("bridge or veth host-side; compare both ends of a veth",
     ["bridge or veth host-side;", "compare both ends of a veth"]),
    ("switch port mirror (SPAN, ERSPAN) or TAP; mirrored traffic can be dropped under congestion",
     ["switch port mirror (SPAN, ERSPAN) or TAP;", "mirrored traffic can be dropped under congestion"]),
    ("NIC or DPU capture: tcpdump -i mlx5_0 with rdma-core, ibdump, or a switch mirror",
     ["NIC or DPU capture: tcpdump -i mlx5_0 with", "rdma-core, ibdump, or a switch mirror"]),
    ("tracepoints, kfree_skb, pwru; complement, do not replace, pcap",
     ["tracepoints, kfree_skb, pwru;", "complement, do not replace, pcap"])
]

avail_w = 790
print("=== RIGHT SIDE (avail_w = 790) ===")
for full, lines in labels_right:
    is_mono = "nsenter" in full or "mlx5_0" in full
    fs = 24
    factor = 0.62 if is_mono else 0.6
    print(f"Label ({len(lines)} lines):")
    for l in lines:
        w = len(l) * fs * factor
        pad = avail_w - w
        assert pad >= 16, f"FAIL: {l} pad={pad}"
        print(f"   '{l}' -> {len(l)}c, {w:.1f}px, pad={pad:.1f}px")
