col_widths = {
    'fabric': 255,
    'l12': 255,
    'l3': 255,
    'l4': 384,
    'nccl': 310
}

# Usable widths (width - 32):
# fabric: 223 px
# l12: 223 px
# l3: 223 px
# l4: 352 px
# nccl: 278 px

test_splits = [
    # Fabrics (col 0):
    ('fabric', 'Ethernet with TCP (front end, storage, control plane)', 24, [
        'Ethernet with',
        'TCP (front end,',
        'storage,',
        'control plane)'
    ]),
    ('fabric', 'RoCE v2', 26, ['RoCE v2']),
    ('fabric', 'InfiniBand', 26, ['InfiniBand']),
    ('fabric', 'NVLink / NVSwitch', 26, ['NVLink /', 'NVSwitch']),
    ('fabric', 'PCIe', 26, ['PCIe']),

    # Headers:
    ('l12', 'L1/L2', 30, ['L1/L2']),
    ('l3', 'L3', 30, ['L3']),
    ('l4', 'L4 and transport', 30, ['L4 and transport']),
    ('nccl', 'NCCL hierarchy', 30, ['NCCL hierarchy']),

    # Row 1 (Ethernet with TCP):
    ('l12', 'Ethernet 25/100/400 GbE', 24, ['Ethernet', '25/100/400 GbE']),
    ('l3', 'IP (BGP/ECMP in Clos)', 24, ['IP (BGP/ECMP', 'in Clos)']),
    ('l4', 'TCP and UDP in the kernel; CUBIC or BBR', 24, ['TCP and UDP in the', 'kernel; CUBIC or BBR']),

    # Row 2 (RoCE v2):
    ('l12', 'Lossless Ethernet (PFC, ECN, DCB)', 24, ['Lossless', 'Ethernet', '(PFC, ECN, DCB)']),
    ('l3', 'IP, routable', 24, ['IP, routable']),
    ('l4', 'UDP 4791 plus IB transport (BTH) in the NIC; RDMA verbs bypass the kernel stack', 24, [
        'UDP 4791 plus IB',
        'transport (BTH) in the',
        'NIC; RDMA verbs bypass',
        'the kernel stack'
    ]),

    # Row 3 (InfiniBand):
    ('l12', 'IB link layer, credit-based, virtual lanes', 24, [
        'IB link layer,',
        'credit-based,',
        'virtual lanes'
    ]),
    ('l3', 'IB network layer, GIDs, LIDs inside subnets, GRH across', 24, [
        'IB network',
        'layer, GIDs,',
        'LIDs inside',
        'subnets, GRH',
        'across'
    ]),
    ('l4', 'IB transport RC/UD in the NIC; Subnet Manager computes forwarding tables', 24, [
        'IB transport RC/UD in',
        'the NIC; Subnet',
        'Manager computes',
        'forwarding tables'
    ]),

    # Row 4 (NVLink / NVSwitch):
    ('l12', 'proprietary GPU-to-GPU links', 24, [
        'proprietary',
        'GPU-to-GPU links'
    ]),
    ('l3', 'no IP, memory-semantic', 24, [
        'no IP,',
        'memory-semantic'
    ]),
    ('l4', 'load/store and DMA between GPUs', 24, [
        'load/store and DMA',
        'between GPUs'
    ]),

    # Row 5 (PCIe):
    ('l12', 'serial links, TLPs', 24, ['serial links,', 'TLPs']),
    ('l3', 'a bus', 24, ['a bus']),
    ('l4', 'GPU-NIC-CPU paths; locality matters', 24, [
        'GPU-NIC-CPU paths;',
        'locality matters'
    ]),

    # NCCL Hierarchy:
    ('nccl', 'NVLink inside the node', 24, ['NVLink inside', 'the node']),
    ('nccl', 'NIC and fabric between nodes', 24, ['NIC and fabric', 'between nodes']),
    ('nccl', 'TCP sockets as the fallback and for bootstrap', 24, [
        'TCP sockets as the',
        'fallback and for',
        'bootstrap'
    ]),
]

all_ok = True
for col, full_label, fs, lines in test_splits:
    w = col_widths[col]
    usable_w = w - 32
    reconstructed = ' '.join(lines)
    if reconstructed != full_label:
        print(f"MISMATCH in reconstructed text:\n  Expected: '{full_label}'\n  Got:      '{reconstructed}'")
        all_ok = False
    for line in lines:
        px = len(line) * 0.6 * fs
        if px > usable_w:
            print(f"OVERFLOW in {col} ({fs}px): '{line}' is {px:.1f}px > {usable_w}px (box {w}px)")
            all_ok = False

if all_ok:
    print("ALL OK! ZERO OVERFLOWS! PERFECT FIT!")
