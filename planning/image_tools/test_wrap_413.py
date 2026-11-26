from test_wrap import est_width

# Card 2 with width 413, pad 20 -> avail_w = 373:
c2_lines = [
    [("per change:", 30, False)],
    [("iptables-restore", 24, True), (" rewrites", 24, False)],
    [("the whole ruleset, takes", 24, False)],
    [("the xtables lock", 24, False)],
    [("(/run/xtables.lock),", 24, True)],
    [("seconds or minutes at", 24, False)], # 302.4px
    [("tens of thousands of rules,", 24, False)], # 388.8px -> let us wrap:
]

# Let's wrap "tens of thousands of rules, can collide with CNI plug-ins and send traffic to stale endpoints" cleanly:
c2_wrap_clean = [
    [("per change:", 30, False)],
    [("iptables-restore", 24, True), (" rewrites", 24, False)],
    [("the whole ruleset, takes the", 24, False)], # 28 * 14.4 = 403.2 > 373
    [("xtables lock", 24, False)],
    [("(/run/xtables.lock),", 24, True)],
    [("seconds or minutes at", 24, False)], # 21 * 14.4 = 302.4
    [("tens of thousands", 24, False)], # 17 * 14.4 = 244.8
    [("of rules, can collide", 24, False)], # 21 * 14.4 = 302.4
    [("with CNI plug-ins and", 24, False)], # 22 * 14.4 = 316.8
    [("send traffic to", 24, False)], # 15 * 14.4 = 216.0
    [("stale endpoints", 24, False)]  # 15 * 14.4 = 216.0
]
for i, l in enumerate(c2_wrap_clean):
    w = est_width(l)
    print(f"C2 line {i+1}: w={w:.1f} (fits 373: {w <= 373})")

