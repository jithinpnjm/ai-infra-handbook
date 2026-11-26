from test_all_rows_detail import rows_data, sidenote_lines

expected = {
    "title": "Ten things to decide for a GPU or HPC pod's network",
    "row1": "1 Primary versus data plane: eth0 for control, secondary RDMA NICs for GPU and storage traffic",
    "row2": "2 NCCL interface selection: NCCL_SOCKET_IFNAME, NCCL_IB_HCA, NCCL_IB_GID_INDEX set explicitly",
    "row3": "3 Host networking: hostNetwork true with dnsPolicy ClusterFirstWithHostNet; simplest high-performance option; costs port conflicts, less isolation, no per-pod NetworkPolicy",
    "row4": "4 Overlay costs: small packets, many connections and large flows suffer crossing a veth, a bridge and an overlay (CPU softirq and a smaller MTU); prefer native routing CNIs or eBPF host routing for TCP-heavy services; overlay MTU is underlay minus 50 for VXLAN; verify with ping -M do",
    "row5": "5 Topology alignment: kubelet Topology Manager single-numa-node or best-effort with the CPU Manager and device plugins keeps GPU, NIC VF and CPUs on the same NUMA node or PCIe root; verify with nvidia-smi topo -m and ibdev2netdev",
    "row6": "6 MTU consistency: pod MTU is node MTU minus encapsulation; secondary rails often 9000 and the CNI mtu must match the fabric",
    "row7": "7 Isolation and policy: NetworkPolicy with default deny per namespace covers the primary network; secondary SR-IOV and macvlan interfaces bypass host policy: isolate with VLANs, VRFs or IB partitions at the switch",
    "row8": "8 IPAM: size the pod CIDR against nodes and pods per node; a /24 per node gives 254 pods; secondary networks may use whereabouts or static ranges, one per rail",
    "row9": "9 Observability: Hubble or Cilium flow logs, Calico flow logs, kube-state and CNI metrics, ethtool -S for VFs, RDMA counters, nsenter into a pod's namespace",
    "row10": "10 Upgrades: CNI changes can reset pod networks; stage them, drain nodes, canary clusters first; keep /opt/cni/bin and /etc/cni/net.d consistent",
    "sidenote": "hostNetwork pods share the node's IP and port space and skip the CNI; node agents such as kube-proxy, the CNI daemon, node-exporter and the DCGM exporter run this way; check for port conflicts before scheduling",
    "bottom_bar": "Decide the rails before you write the pod spec"
}

all_match = True
for idx, (row_num, title, rule_lines, is_orange) in enumerate(rows_data, 1):
    full = title + " " + " ".join(rule_lines)
    exp = expected[f"row{idx}"]
    if full != exp:
        print(f"MISMATCH in row {idx}:")
        print(f"  Got: {full}")
        print(f"  Exp: {exp}")
        all_match = False
    else:
        print(f"Row {idx:2d} matches exactly!")

sn_full = " ".join(sidenote_lines)
if sn_full != expected["sidenote"]:
    print(f"MISMATCH in sidenote:")
    print(f"  Got: {sn_full}")
    print(f"  Exp: {expected['sidenote']}")
    all_match = False
else:
    print("Side note matches exactly!")

if all_match:
    print("\nALL LABELS MATCH EXACTLY!")
