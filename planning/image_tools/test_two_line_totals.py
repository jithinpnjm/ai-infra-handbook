# Let's test if Title + Rule can start on Line 1 and continue on Line 2!

# In Row 8:
# Title: "8 IPAM: " (8 chars * 18 = 144px)
# Rule: "size the pod CIDR against nodes and pods per node; a /24 per node gives 254 pods; secondary networks may use whereabouts or static ranges, one per rail" (151 chars)
# Can rule be split into 2 lines?
# Line 1: 8 IPAM: size the pod CIDR against nodes and pods per node; a /24 per node gives (81 chars)
# Line 2: 254 pods; secondary networks may use whereabouts or static ranges, one per rail (77 chars)
# Check width:
# Line 1: 8 chars * 18 + 73 chars * 14.4 = 144 + 1051.2 = 1195.2px <= 1428px!
# Line 2: 77 chars * 14.4 = 1108.8px <= 1428px!
# ROW 8 IS ONLY 2 LINES!

# In Row 9:
# Title: "9 Observability: " (17 chars * 18 = 306px)
# Line 1: 9 Observability: Hubble or Cilium flow logs, Calico flow logs, kube-state and (79 chars)
#   Width = 17 * 18 + 62 * 14.4 = 306 + 892.8 = 1198.8px <= 1428px!
# Line 2: CNI metrics, ethtool -S for VFs, RDMA counters, nsenter into a pod's namespace (76 chars)
#   Width = 76 * 14.4 = 1094.4px <= 1428px!
# ROW 9 IS ONLY 2 LINES!

# In Row 10:
# Title: "10 Upgrades: " (13 chars * 18 = 234px)
# Line 1: 10 Upgrades: CNI changes can reset pod networks; stage them, drain nodes, canary (80 chars)
#   Width = 13 * 18 + 67 * 14.4 = 234 + 964.8 = 1198.8px <= 1428px!
# Line 2: clusters first; keep /opt/cni/bin and /etc/cni/net.d consistent (63 chars)
#   Width = 63 * 14.4 = 907.2px <= 1428px!
# ROW 10 IS ONLY 2 LINES!

# In Row 6:
# Title: "6 MTU consistency: " (19 chars * 18 = 342px)
# Line 1: 6 MTU consistency: pod MTU is node MTU minus encapsulation; secondary rails (78 chars)
#   Width = 19 * 18 + 59 * 14.4 = 342 + 849.6 = 1191.6px <= 1428px!
# Line 2: often 9000 and the CNI mtu must match the fabric (45 chars)
#   Width = 45 * 14.4 = 648px <= 1428px!
# ROW 6 IS ONLY 2 LINES!

# In Row 1:
# Title: "1 Primary versus data plane: " (29 chars * 18 = 522px)
# Line 1: 1 Primary versus data plane: eth0 for control, secondary RDMA (63 chars)
#   Width = 29 * 18 + 34 * 14.4 = 522 + 489.6 = 1011.6px <= 1428px!
# Line 2: NICs for GPU and storage traffic (31 chars)
#   Width = 31 * 14.4 = 446.4px <= 1428px!
# ROW 1 IS ONLY 2 LINES!

# In Row 2:
# Title: "2 NCCL interface selection: " (28 chars * 18 = 504px)
# Line 1: 2 NCCL interface selection: NCCL_SOCKET_IFNAME, NCCL_IB_HCA, (62 chars)
#   Width = 28 * 18 + 34 * 14.4 = 504 + 489.6 = 993.6px <= 1428px!
# Line 2: NCCL_IB_GID_INDEX set explicitly (32 chars)
#   Width = 32 * 14.4 = 460.8px <= 1428px!
# ROW 2 IS ONLY 2 LINES!

# In Row 7:
# Title: "7 Isolation and policy: " (24 chars * 18 = 432px)
# Line 1: 7 Isolation and policy: NetworkPolicy with default deny per namespace (70 chars)
#   Width = 24 * 18 + 46 * 14.4 = 432 + 662.4 = 1094.4px <= 1428px!
# Line 2: covers the primary network; secondary SR-IOV and macvlan interfaces bypass host (81 chars)
#   Width = 81 * 14.4 = 1166.4px <= 1428px!
# Line 3: policy: isolate with VLANs, VRFs or IB partitions at the switch (63 chars)
#   Width = 63 * 14.4 = 907.2px <= 1428px!
# ROW 7 IS ONLY 3 LINES!

# In Row 5:
# Title: "5 Topology alignment: " (22 chars * 18 = 396px)
# Line 1: 5 Topology alignment: kubelet Topology Manager single-numa-node or (67 chars)
#   Width = 22 * 18 + 45 * 14.4 = 396 + 648 = 1044px <= 1428px!
# Line 2: best-effort with the CPU Manager and device plugins keeps GPU, NIC VF and CPUs (79 chars)
#   Width = 79 * 14.4 = 1137.6px <= 1428px!
# Line 3: on the same NUMA node or PCIe root; verify with nvidia-smi topo -m and ibdev2netdev (82 chars)
#   Width = 82 * 14.4 = 1180.8px <= 1428px!
# ROW 5 IS ONLY 3 LINES!

# In Row 4:
# Title: "4 Overlay costs: " (17 chars * 18 = 306px)
# Line 1: 4 Overlay costs: small packets, many connections and large flows suffer crossing a (84 chars)
#   Width = 17 * 18 + 67 * 14.4 = 306 + 964.8 = 1270.8px <= 1428px!
# Line 2: veth, a bridge and an overlay (CPU softirq and a smaller MTU); prefer native routing CNIs (89 chars)
#   Width = 89 * 14.4 = 1281.6px <= 1428px!
# Line 3: or eBPF host routing for TCP-heavy services; overlay MTU is underlay minus 50 for (82 chars)
#   Width = 82 * 14.4 = 1180.8px <= 1428px!
# Line 4: VXLAN; verify with ping -M do (29 chars)
#   Width = 29 * 14.4 = 417.6px <= 1428px!
# ROW 4 IS 4 LINES!

print("Calculated line counts for all rows:")
print("Row 1: 2 lines")
print("Row 2: 2 lines")
print("Row 4: 4 lines")
print("Row 5: 3 lines")
print("Row 6: 2 lines")
print("Row 7: 3 lines")
print("Row 8: 2 lines")
print("Row 9: 2 lines")
print("Row 10: 2 lines")
