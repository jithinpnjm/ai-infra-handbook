import re
import xml.etree.ElementTree as ET

# List of expected labels from spec:
labels = [
    "A full conntrack table: new connections fail, old ones keep working",
    "conntrack table (hash table)",
    "nf_conntrack_count = nf_conntrack_max",
    "source address, source port, destination address, destination port, protocol",
    "established flow: keeps its slot, works",
    "new connection: no space, cannot be made",
    "1 Read the two numbers: sysctl net.netfilter.nf_conntrack_count and nf_conntrack_max",
    "2 Divide: count / max",
    "3 Watch the trend: read twice; climbing and staying = flows arrive faster than they leave; rising then falling = a burst",
    "Established timeout default: 432000 seconds, five days",
    "Kube-proxy Service load balancing through iptables depends on conntrack, so a full table looks like Service flakiness; pods on one node share that node's table.",
    "raise the maximum if memory allows, reuse connections, find the client opening connections in a loop",
    "For any new connections fail, old ones work symptom, compare conntrack count to max first."
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. len={len(l):3d} : '{l}'")
