def w(s): return len(s) * 24 * 0.6

lines = [
    (125, "Docker's own NAT and"),
    (125, "FORWARD rules (DOCKER"),
    (75, "chain) are inserted ahead"),
    (75, "of the rules managed by"),
    (75, "ufw or firewalld")
]

box_right = 500
for x, text in lines:
    right_edge = x + w(text)
    pad = box_right - right_edge
    print(f"x={x:3d}, w={w(text):5.1f}px, right={right_edge:5.1f}px, pad={pad:5.1f}px : {text}")
