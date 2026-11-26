#!/usr/bin/env python3
import re

labels = [
    "Keeping the GPU, its NIC and its CPUs on one NUMA node",
    "NUMA node 0",
    "NUMA node 1",
    "Aligned",
    "GPU, NIC VF or RDMA device, and the pod's CPUs all on NUMA node 0",
    "transfers stay inside the node; fast",
    "Misaligned",
    "pod CPUs on node 0 but the NIC on node 1",
    "every transfer crosses the link between sockets and takes the slower road",
    "how to keep them together",
    "kubelet Topology Manager with the single-numa-node or best-effort policy, together with the CPU Manager and the device plugins",
    "Verify after the pod starts: nvidia-smi topo -m, ibdev2netdev",
    "same on the host: pin test CPUs to the NUMA node of the NIC",
    "A scheduler can place CPUs on one node and the network card on the other, so check the placement after the pod starts"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. [{len(l):3d} chars] '{l}'")

forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for l in labels:
    words = re.findall(r'\b[a-zA-Z]+\b', l.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{l}'"

print("All labels clean of forbidden style words!")
