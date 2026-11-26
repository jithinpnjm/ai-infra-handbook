# Let's verify all strings from the user prompt:
# Check spelling against user prompt:

prompt_strings = [
    # Shared host components
    "br0 (10.10.0.1/24)",
    "c1 (10.10.0.11)",
    "c2 (10.10.0.12)",
    "uplink NIC",
    "host",
    # Lane 1
    "c1 to c2 on the same bridge",
    "c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame to c2's veth and eth0",
    "br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic; Kubernetes requires it so kube-proxy rules apply",
    # Lane 2
    "c1 to the Internet",
    "default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed by conntrack and delivered back through the bridge; the outside world only talks to the host",
    "sysctl -w net.ipv4.ip_forward=1",
    "iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE",
    "iptables -I FORWARD -i br0 -j ACCEPT",
    "iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
    # Lane 3
    "host:8080 to c1:80",
    "iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.10.0.11:80",
    "iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 8080 -j DNAT ... for local clients",
    # Footer
    "DNS inside: mkdir /etc/netns/c1 and write nameserver 1.1.1.1 to /etc/netns/c1/resolv.conf",
    # Docker note
    "almost literally what the default bridge network does: docker0, a veth per container, an IPAM address from a private pool, a default route via the bridge, masquerade, DNAT for published ports, a bind-mounted /etc/resolv.conf",
    # Bottom bar
    "A container is only a namespace plus a cable"
]

print(f"Total core content items: {len(prompt_strings)}")
for s in prompt_strings:
    print(" -", s[:60] + ("..." if len(s) > 60 else ""))
