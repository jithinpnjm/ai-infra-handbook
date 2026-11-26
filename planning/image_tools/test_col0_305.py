# Let's check widths if Col 0 is 305 px:
# Canvas width = 1600. Margins = 40 left, 40 right -> 1520 total width.
# Col 0 (Fabric): x = 40, w = 305 (usable = 273)
# Col 1 (L1/L2): x = 355, w = 250 (usable = 218)
# Col 2 (L3): x = 615, w = 250 (usable = 218)
# Col 3 (L4): x = 875, w = 365 (usable = 333)
# Total table width = 305 + 10 + 250 + 10 + 250 + 10 + 365 = 1200 px!
# Gap = 25 px
# Right strip (NCCL): x = 1265, w = 295 (usable = 263)
# 1265 + 295 = 1560 (+ 40 margin = 1600).
# Let's verify all lines fit:
lines_col0 = ['Ethernet with', 'TCP (front end,', 'storage,', 'control plane)']
for l in lines_col0:
    px = len(l) * 0.6 * 30
    assert px <= 273, f"Col 0 overflow: {l} ({px} > 273)"

lines_col1 = [
    ['Ethernet', '25/100/400 GbE'],
    ['Lossless', 'Ethernet', '(PFC, ECN, DCB)'],
    ['IB link layer,', 'credit-based,', 'virtual lanes'],
    ['proprietary', 'GPU-to-GPU', 'links'],
    ['serial links,', 'TLPs']
]
for group in lines_col1:
    for l in group:
        px = len(l) * 0.6 * 24
        assert px <= 218, f"Col 1 overflow: {l} ({px} > 218)"

lines_col2 = [
    ['IP (BGP/ECMP', 'in Clos)'],
    ['IP, routable'],
    ['IB network', 'layer, GIDs,', 'LIDs inside', 'subnets, GRH', 'across'],
    ['no IP,', 'memory-semantic'],
    ['a bus']
]
for group in lines_col2:
    for l in group:
        px = len(l) * 0.6 * 24
        assert px <= 218, f"Col 2 overflow: {l} ({px} > 218)"

lines_col3 = [
    ['TCP and UDP in the', 'kernel; CUBIC or BBR'],
    ['UDP 4791 plus IB', 'transport (BTH) in the', 'NIC; RDMA verbs bypass', 'the kernel stack'],
    ['IB transport RC/UD in', 'the NIC; Subnet', 'Manager computes', 'forwarding tables'],
    ['load/store and DMA', 'between GPUs'],
    ['GPU-NIC-CPU paths;', 'locality matters']
]
for group in lines_col3:
    for l in group:
        px = len(l) * 0.6 * 24
        assert px <= 333, f"Col 3 overflow: {l} ({px} > 333)"

lines_nccl = [
    ['NVLink inside', 'the node'],
    ['NIC and fabric', 'between nodes'],
    ['TCP sockets as the', 'fallback and for', 'bootstrap']
]
for group in lines_nccl:
    for l in group:
        px = len(l) * 0.6 * 24
        assert px <= 263, f"NCCL overflow: {l} ({px} > 263)"

print("ALL FABRIC TITLES CAN BE 30 PX BOLD WITH ZERO OVERFLOW!")
