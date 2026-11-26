l2_desc = [
    "default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD then",
    "POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed",
    "by conntrack and delivered back through the bridge; the outside world only talks to the host"
]
print("L2 desc match:", " ".join(l2_desc) == "default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed by conntrack and delivered back through the bridge; the outside world only talks to the host")
for l in l2_desc:
    print("desc line:", len(l), len(l)*24*0.6)

cmds = [
    "sysctl -w net.ipv4.ip_forward=1",
    "iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE",
    "iptables -I FORWARD -i br0 -j ACCEPT",
    "iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT"
]
for c in cmds:
    print("cmd line:", len(c), len(c)*24*0.62)
