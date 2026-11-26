# Let's test inline flow where each row has:
# Icon at left (x = 55 to 105)
# Text starts at x = 120, width available = 1540 - 120 = 1420 px!
# At font 24 (14.4 px/char) -> max_chars = 96!

items = [
    "1 Primary versus data plane: eth0 for control, secondary RDMA NICs for GPU and storage traffic",
    "2 NCCL interface selection: NCCL_SOCKET_IFNAME, NCCL_IB_HCA, NCCL_IB_GID_INDEX set explicitly",
    "3 Host networking: hostNetwork true with dnsPolicy ClusterFirstWithHostNet; simplest high-performance option; costs port conflicts, less isolation, no per-pod NetworkPolicy",
    "4 Overlay costs: small packets, many connections and large flows suffer crossing a veth, a bridge and an overlay (CPU softirq and a smaller MTU); prefer native routing CNIs or eBPF host routing for TCP-heavy services; overlay MTU is underlay minus 50 for VXLAN; verify with ping -M do",
    "5 Topology alignment: kubelet Topology Manager single-numa-node or best-effort with the CPU Manager and device plugins keeps GPU, NIC VF and CPUs on the same NUMA node or PCIe root; verify with nvidia-smi topo -m and ibdev2netdev",
    "6 MTU consistency: pod MTU is node MTU minus encapsulation; secondary rails often 9000 and the CNI mtu must match the fabric",
    "7 Isolation and policy: NetworkPolicy with default deny per namespace covers the primary network; secondary SR-IOV and macvlan interfaces bypass host policy: isolate with VLANs, VRFs or IB partitions at the switch",
    "8 IPAM: size the pod CIDR against nodes and pods per node; a /24 per node gives 254 pods; secondary networks may use whereabouts or static ranges, one per rail",
    "9 Observability: Hubble or Cilium flow logs, Calico flow logs, kube-state and CNI metrics, ethtool -S for VFs, RDMA counters, nsenter into a pod's namespace",
    "10 Upgrades: CNI changes can reset pod networks; stage them, drain nodes, canary clusters first; keep /opt/cni/bin and /etc/cni/net.d consistent"
]

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

for i, item in enumerate(items, 1):
    w_chars = 95
    lines = wrap_text(item, w_chars)
    print(f"Row {i:2d} ({len(lines)} lines):")
    for l in lines:
        print(f"   [{len(l):2d}] {l}")
