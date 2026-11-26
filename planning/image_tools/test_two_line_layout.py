def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

rows = [
    ("1 Primary versus data plane:", "eth0 for control, secondary RDMA NICs for GPU and storage traffic"),
    ("2 NCCL interface selection:", "NCCL_SOCKET_IFNAME, NCCL_IB_HCA, NCCL_IB_GID_INDEX set explicitly"),
    ("3 Host networking:", "hostNetwork true with dnsPolicy ClusterFirstWithHostNet; simplest high-performance option; costs port conflicts, less isolation, no per-pod NetworkPolicy"),
    ("4 Overlay costs:", "small packets, many connections and large flows suffer crossing a veth, a bridge and an overlay (CPU softirq and a smaller MTU); prefer native routing CNIs or eBPF host routing for TCP-heavy services; overlay MTU is underlay minus 50 for VXLAN; verify with ping -M do"),
    ("5 Topology alignment:", "kubelet Topology Manager single-numa-node or best-effort with the CPU Manager and device plugins keeps GPU, NIC VF and CPUs on the same NUMA node or PCIe root; verify with nvidia-smi topo -m and ibdev2netdev"),
    ("6 MTU consistency:", "pod MTU is node MTU minus encapsulation; secondary rails often 9000 and the CNI mtu must match the fabric"),
    ("7 Isolation and policy:", "NetworkPolicy with default deny per namespace covers the primary network; secondary SR-IOV and macvlan interfaces bypass host policy: isolate with VLANs, VRFs or IB partitions at the switch"),
    ("8 IPAM:", "size the pod CIDR against nodes and pods per node; a /24 per node gives 254 pods; secondary networks may use whereabouts or static ranges, one per rail"),
    ("9 Observability:", "Hubble or Cilium flow logs, Calico flow logs, kube-state and CNI metrics, ethtool -S for VFs, RDMA counters, nsenter into a pod's namespace"),
    ("10 Upgrades:", "CNI changes can reset pod networks; stage them, drain nodes, canary clusters first; keep /opt/cni/bin and /etc/cni/net.d consistent")
]

sidenote = "hostNetwork pods share the node's IP and port space and skip the CNI; node agents such as kube-proxy, the CNI daemon, node-exporter and the DCGM exporter run this way; check for port conflicts before scheduling"

# In Row 3 + Side note:
# Row 3 is on left: x=40, w=880. Text at x=120, w=740 -> max_chars = 740 / 14.4 = 51 chars
# Side note is on right: x=940, w=620. Text at x=965, w=570 -> max_chars = 570 / 14.4 = 39 chars

# In other rows:
# Width = 1520. Text at x=120, w=1420 -> max_chars = 1420 / 14.4 = 98 chars

print("--- Check line counts and heights ---")
total_h = 0
row_configs = []
for i in range(10):
    t, r = rows[i]
    if i == 2: # Row 3
        r_lines = wrap_text(r, 51)
        # Row 3 height:
        # Title (30px): 34px
        # Rule (24px): len(r_lines) * 28px
        # Plus padding: 24px
        # But must match side note height!
        sn_lines = wrap_text(sidenote, 39)
        sn_h = len(sn_lines) * 27 + 28
        r3_h = 34 + len(r_lines) * 27 + 24
        h = max(r3_h, sn_h)
        print(f"Row {i+1:2d} (w=880): Title 1 line, Rule {len(r_lines)} lines, SideNote {len(sn_lines)} lines -> h={h}px")
    else:
        r_lines = wrap_text(r, 96)
        # Title 1 line (30px): 34px
        # Rule (24px): len(r_lines) * 27px
        # Padding: 22px
        h = 32 + len(r_lines) * 27 + 22
        print(f"Row {i+1:2d} (w=1520): Title 1 line, Rule {len(r_lines)} lines -> h={h}px")
    row_configs.append(h)
    total_h += h

gap = 6
total_table_h = sum(row_configs) + gap * 9
print(f"\nTotal table height: {total_table_h}px")

title_h = 60
bb_h = 44
total_svg_h = title_h + 16 + total_table_h + 14 + bb_h + 16
print(f"Total SVG height = {total_svg_h}px (must be <= 1200)")

