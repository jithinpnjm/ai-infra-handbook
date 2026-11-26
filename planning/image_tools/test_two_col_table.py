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

# Table geometry:
# In rows 1, 2, 4-10:
# Total width = 1520.
# Col 1: Icon (x=55, w=50) + Decision Title (x=120, w=380). Max chars = 21 at 30px (0.6*30 = 18px -> 380/18 = 21 chars)
# Col 2: Rule (x=530, w=990). Max chars = 990 / 14.4 = 68 chars at 24px.
#
# In row 3:
# Row 3 is on left: x=40, w=920.
# Col 1: Icon (x=55, w=50) + Title (x=120, w=320, max_chars = 17)
# Col 2: Rule (x=460, w=480, max_chars = 480 / 14.4 = 33 chars)
# Side note is on right: x=980, w=580.
# Text at x=1004, w=532. Max chars = 532 / 14.4 = 36 chars.

print("--- Check lines ---")
row_details = []
for i in range(10):
    t, r = rows[i]
    if i == 2:
        t_lines = wrap_text(t, 18)
        r_lines = wrap_text(r, 34)
    else:
        t_lines = wrap_text(t, 22)
        r_lines = wrap_text(r, 68)
    
    # Calculate height:
    # Title height = len(t_lines) * 34
    # Rule height = len(r_lines) * 28
    # Content height = max(title_height, rule_height)
    content_h = max(len(t_lines) * 34, len(r_lines) * 28)
    # Row 3 must also match side note height if needed
    h = content_h + 34 # 17px top, 17px bottom padding
    if i == 2:
        # Check side note height:
        sn = "hostNetwork pods share the node's IP and port space and skip the CNI; node agents such as kube-proxy, the CNI daemon, node-exporter and the DCGM exporter run this way; check for port conflicts before scheduling"
        sn_lines = wrap_text(sn, 36)
        sn_h = len(sn_lines) * 26 + 34
        h = max(h, sn_h)
    row_details.append((t_lines, r_lines, h))
    print(f"Row {i+1:2d}: Title {len(t_lines)} lines, Rule {len(r_lines)} lines -> h={h}px")

gap = 6
total_table_h = sum(d[2] for d in row_details) + gap * 9
print(f"\nTotal table height: {total_table_h}px")
title_h = 60
bb_h = 44
print(f"Total SVG height = {title_h + 16 + total_table_h + 14 + bb_h + 16}px")
