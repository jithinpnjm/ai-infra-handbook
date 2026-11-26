lines_desc = [
    "c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves",
    "c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame",
    "to c2's veth and eth0"
]
line_note = [
    "br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic;",
    "Kubernetes requires it so kube-proxy rules apply"
]

print("Desc recombined matches original:", " ".join(lines_desc) == "c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame to c2's veth and eth0")
print("Note recombined matches original:", " ".join(line_note) == "br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic; Kubernetes requires it so kube-proxy rules apply")

for l in lines_desc:
    print("desc line:", len(l), len(l)*24*0.6)
for l in line_note:
    print("note line:", len(l), len(l)*24*0.6)
