def check_wrap(text, box_width, font_size=24):
    char_w = 0.6 * font_size
    usable_w = box_width - 32
    max_chars = int(usable_w / char_w)
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur and (cur_len + 1 + len(w)) > max_chars:
            lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len = len(' '.join(cur))
    if cur:
        lines.append(' '.join(cur))
    overflow = False
    for i, l in enumerate(lines):
        px = len(l) * char_w
        if px > usable_w:
            overflow = True
        print(f"  Line {i+1} ({len(l)} chars, {px:.1f}px / {usable_w}px): '{l}'")
    if overflow:
        print("  !!! OVERFLOW DETECTED !!!")
    return lines

print("=== Col 0 (width 250) ===")
check_wrap("Ethernet with TCP (front end, storage, control plane)", 250)
check_wrap("RoCE v2", 250)
check_wrap("InfiniBand", 250)
check_wrap("NVLink / NVSwitch", 250)
check_wrap("PCIe", 250)

print("\n=== Col 1 (width 260) ===")
check_wrap("Ethernet 25/100/400 GbE", 260)
check_wrap("Lossless Ethernet (PFC, ECN, DCB)", 260)
check_wrap("IB link layer, credit-based, virtual lanes", 260)
check_wrap("proprietary GPU-to-GPU links", 260)
check_wrap("serial links, TLPs", 260)

print("\n=== Col 2 (width 260) ===")
check_wrap("IP (BGP/ECMP in Clos)", 260)
check_wrap("IP, routable", 260)
check_wrap("IB network layer, GIDs, LIDs inside subnets, GRH across", 260)
check_wrap("no IP, memory-semantic", 260)
check_wrap("a bus", 260)

print("\n=== Col 3 (width 380) ===")
check_wrap("TCP and UDP in the kernel; CUBIC or BBR", 380)
check_wrap("UDP 4791 plus IB transport (BTH) in the NIC; RDMA verbs bypass the kernel stack", 380)
check_wrap("IB transport RC/UD in the NIC; Subnet Manager computes forwarding tables", 380)
check_wrap("load/store and DMA between GPUs", 380)
check_wrap("GPU-NIC-CPU paths; locality matters", 380)

print("\n=== Right Strip (width 340) ===")
check_wrap("NVLink inside the node", 340)
check_wrap("NIC and fabric between nodes", 340)
check_wrap("TCP sockets as the fallback and for bootstrap", 340)
