#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

expected_labels = [
    "Bridge CNI versus routed CNI on one node",
    "Bridge-based CNI (bridge, Flannel host-gw)",
    "pod A eth0 (a veth)",
    "host-side vethXXX on bridge cni0",
    "pod B's veth",
    "pod B",
    "the node's pod CIDR such as 10.244.1.0/24 is local and the bridge IP is the gateway",
    "Routed CNI (Calico)",
    "no bridge",
    "each pod gets a /32 route on the host, such as 10.244.1.5 dev caliXXXX scope link",
    "proxy ARP answers the pod's ARP request for its default gateway at 169.254.1.1",
    "pod, veth, host routing, veth, pod",
    "pod default route via 169.254.1.1 dev eth0 onlink; proxy_arp on the host-side veths",
    "Cross-node: overlay (VXLAN, IPIP, Geneve) wraps the packet in an outer packet addressed to the other node: a route such as 10.244.2.0/24 via flannel.1, tunl0 or vxlan.calico, encapsulated in UDP or IP-in-IP; costs: MTU, CPU, pod IPs the fabric cannot see. Routed: node 1 holds 10.244.2.0/24 via <node2 IP> (static config, BIRD or the CNI daemon); needs L2 adjacency for host-gw, or a fabric learning pod prefixes over BGP; best performance, pod IPs visible in the fabric for firewalling and monitoring. Cloud-native: pod IPs come from the VPC subnet",
    "ip route | grep 10.244",
    "bridge fdb show dev flannel.1",
    "tcpdump -ni eth0 udp port 8472 (Flannel, Cilium VXLAN) or 4789",
    "Same pod to pod result, two different data paths"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. {l}")
