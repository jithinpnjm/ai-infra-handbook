d = "default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed by conntrack and delivered back through the bridge; the outside world only talks to the host"
w1 = "default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD"
w2 = "then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed"
w3 = "by conntrack and delivered back through the bridge; the outside world only talks to the host"

print("Matches:", " ".join([w1, w2, w3]) == d)
for w in [w1, w2, w3]:
    print(f"len={len(w)}, px={len(w)*24*0.6:.1f}")
