usable_w = 314 - 32 # 282 px
fs = 24
char_w = 0.6 * fs # 14.4 px

lines_col3 = [
    # TCP and UDP
    "TCP and UDP in the",
    "kernel; CUBIC or BBR",
    
    # UDP 4791
    "UDP 4791 plus IB",
    "transport (BTH) in",
    "the NIC; RDMA verbs",
    "bypass the kernel stack",
    
    # IB transport
    "IB transport RC/UD in",
    "the NIC; Subnet Manager",
    "computes forwarding",
    "tables",
    
    # load/store
    "load/store and DMA",
    "between GPUs",
    
    # GPU-NIC-CPU
    "GPU-NIC-CPU paths;",
    "locality matters"
]

for l in lines_col3:
    px = len(l) * char_w
    status = "OK" if px <= usable_w else "OVERFLOW"
    print(f"'{l}': {px:.1f}px / {usable_w}px ({status})")
    if status == "OVERFLOW":
        print("  --> OVERFLOWED!")
