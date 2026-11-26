from test_strict_geometry import test_box_padding

# Bottom Takeaway Bar (by=1025, bh=95)
bottom_lines = [
    "A refusal means the host answered, so look at the listener; a timeout means the SYNs never got",
    "a reply, so look at the route and firewall"
]
test_box_padding("Bottom Bar", 40, 1025, 1520, 95, bottom_lines, 26, [1062, 1092], anchor="middle")

print("BOTTOM BAR PASSED!")
