import xml.etree.ElementTree as ET
import re

spec_labels = [
    "Three log shapes worth recognising",
    "Node flapping",
    "slurmctld: error: Nodes dgx-h100-14 not responding",
    "slurmctld: Node dgx-h100-14 now responding",
    "rarely Slurm: packets dropped on the management network, or the node so loaded that slurmd cannot answer the ping in time",
    "investigate the network and node CPU and I/O load before touching Slurm settings; changing a timeout to hide a flapping node hides the fault",
    "Job killed for memory",
    "slurmd log shows a step dying with signal 9 and a memory-limit message for the job's cgroup",
    "user asked for less memory than the job used; the kernel out-of-memory killer acting at the cgroup limit ended the job",
    "Invalid RPC after an upgrade",
    "a compute node logs it received an RPC it does not understand or a message with zero bytes; version mismatch; slurmd must never be newer than slurmctld; nodes may be older than the controller during a rolling upgrade",
    "exact wording differs between versions; learn the shape"
]

print("Total spec labels:", len(spec_labels))
for i, l in enumerate(spec_labels, 1):
    print(f"{i:2d}. {l}")
