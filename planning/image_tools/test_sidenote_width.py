from test_inline_flow import wrap_text

sidenote = "hostNetwork pods share the node's IP and port space and skip the CNI; node agents such as kube-proxy, the CNI daemon, node-exporter and the DCGM exporter run this way; check for port conflicts before scheduling"

# If Side note width is 740:
# Text starts at x = 860 + 26 = 886. Available width = 740 - 30 - 20 = 690px.
# At 14.4 px/char: 690 / 14.4 = 47.9 -> 47 chars per line!
sn_lines = wrap_text(sidenote, 47)
print(f"Side note in 740px ({len(sn_lines)} lines):")
for l in sn_lines:
    print(f"  [{len(l)}] {l}")

# If Side note is 5 lines:
# line 1: 36
# line 2: 62
# line 3: 88
# line 4: 114
# line 5: 140
# rh = 140 + 16 = 156px!
# That saves 182 - 156 = 26px!

# Can Side note be 4 lines if width is 840?
sn_lines4 = wrap_text(sidenote, 60)
print(f"\nSide note in 840px ({len(sn_lines4)} lines):")
for l in sn_lines4:
    print(f"  [{len(l)}] {l}")

