# Check all text lines in Lane 1, Lane 2, Lane 3 if starting at x=60 or x=116:

box_x2 = 1560 # right edge of all boxes

# In Lane 1:
lane1_lines = [
    "c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves",
    "c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame",
    "to c2's veth and eth0",
    "br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic;",
    "Kubernetes requires it so kube-proxy rules apply"
]

print("Lane 1 lines from x=70:")
for l in lane1_lines:
    w = len(l) * 24 * 0.6
    print(f"  len={len(l)}, width={w:.1f}, right_edge={70+w:.1f}, pad_right={box_x2 - (70+w):.1f}")
    assert box_x2 - (70+w) >= 16

