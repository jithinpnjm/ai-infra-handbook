strip_text = "BGP convergence sets how quickly a failed node's traffic moves; BFD detects in under a second; resilient or consistent hashing in the router moves only the failed node's flows; announce the VIP only while the node can serve; a route change can move a flow to a different site, which breaks long-lived TCP; fabric ECMP caveats: elephant flows, RoCE varies UDP source ports per QP, tunnels need inner-header hashing, adaptive routing reacts to load"

# Let's break naturally at semicolons or punctuation:
# 1. BGP convergence sets how quickly a failed node's traffic moves; BFD detects in under a second;
# 2. resilient or consistent hashing in the router moves only the failed node's flows;
# 3. announce the VIP only while the node can serve; a route change can move a flow to a different site,
# 4. which breaks long-lived TCP; fabric ECMP caveats: elephant flows, RoCE varies UDP source ports per QP,
# 5. tunnels need inner-header hashing, adaptive routing reacts to load

lines = [
    "BGP convergence sets how quickly a failed node's traffic moves; BFD detects in under a second;",
    "resilient or consistent hashing in the router moves only the failed node's flows;",
    "announce the VIP only while the node can serve; a route change can move a flow to a different site,",
    "which breaks long-lived TCP; fabric ECMP caveats: elephant flows, RoCE varies UDP source ports per QP,",
    "tunnels need inner-header hashing, adaptive routing reacts to load"
]

print("Joined equals original?:", " ".join(lines) == strip_text)
available = 1520 - 48 # 1472
for i, l in enumerate(lines, 1):
    lw = len(l) * 0.6 * 24
    pad = (1520 - lw) / 2
    print(f"Line {i}: len={len(l):2d}, lw={lw:6.1f}px / {available}px (pad={pad:.1f}px) | '{l}'")
