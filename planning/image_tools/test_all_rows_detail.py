rows_data = [
    # (row_num, title, rule, n_rule_lines, is_orange)
    (1, "1 Primary versus data plane:", 
     ["eth0 for control, secondary RDMA NICs for GPU and storage traffic"], False),
    (2, "2 NCCL interface selection:", 
     ["NCCL_SOCKET_IFNAME, NCCL_IB_HCA, NCCL_IB_GID_INDEX set explicitly"], False),
    (3, "3 Host networking:", 
     ["hostNetwork true with dnsPolicy",
      "ClusterFirstWithHostNet; simplest high-performance",
      "option; costs port conflicts, less isolation, no",
      "per-pod NetworkPolicy"], False),
    (4, "4 Overlay costs:", 
     ["small packets, many connections and large flows suffer crossing a veth, a bridge and an",
      "overlay (CPU softirq and a smaller MTU); prefer native routing CNIs or eBPF host routing for",
      "TCP-heavy services; overlay MTU is underlay minus 50 for VXLAN; verify with ping -M do"], False),
    (5, "5 Topology alignment:", 
     ["kubelet Topology Manager single-numa-node or best-effort with the CPU Manager and device plugins",
      "keeps GPU, NIC VF and CPUs on the same NUMA node or PCIe root; verify with nvidia-smi topo -m and",
      "ibdev2netdev"], False),
    (6, "6 MTU consistency:", 
     ["pod MTU is node MTU minus encapsulation; secondary rails often 9000 and the CNI mtu must",
      "match the fabric"], False),
    (7, "7 Isolation and policy:", 
     ["NetworkPolicy with default deny per namespace covers the primary network; secondary SR-IOV and",
      "macvlan interfaces bypass host policy: isolate with VLANs, VRFs or IB partitions at the switch"], True),
    (8, "8 IPAM:", 
     ["size the pod CIDR against nodes and pods per node; a /24 per node gives 254 pods; secondary",
      "networks may use whereabouts or static ranges, one per rail"], False),
    (9, "9 Observability:", 
     ["Hubble or Cilium flow logs, Calico flow logs, kube-state and CNI metrics, ethtool -S for VFs,",
      "RDMA counters, nsenter into a pod's namespace"], False),
    (10, "10 Upgrades:", 
     ["CNI changes can reset pod networks; stage them, drain nodes, canary clusters first; keep",
      "/opt/cni/bin and /etc/cni/net.d consistent"], False),
]

sidenote_lines = [
    "hostNetwork pods share the node's IP and",
    "port space and skip the CNI; node agents",
    "such as kube-proxy, the CNI daemon,",
    "node-exporter and the DCGM exporter",
    "run this way; check for port conflicts",
    "before scheduling"
]

print("Verifying text reconstruction:")
for row_num, title, rule_lines, is_orange in rows_data:
    full = title + " " + " ".join(rule_lines)
    print(f"Row {row_num:2d}: {full[:60]}... ({len(full)} chars)")

sn_full = " ".join(sidenote_lines)
print(f"Side note: {sn_full[:60]}... ({len(sn_full)} chars)")
