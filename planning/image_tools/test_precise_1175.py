from calc_table import wrap_text, rows

# Let's test the exact layout:
# Width = 1600, Height = 1200.
# Background #f5f8f5
# Title at y = 52 (font-size 48, bold)
# Bottom bar at y = 1140, h = 48 (x=40 to 1560, fill=#207448)

# Table starts at y = 80
# Rows 1, 2: width 1520 (x=40 to 1560)
# Row 3: width 950 (x=40 to 990)
# Side note: width 550 (x=1010 to 1560), same y as Row 3!
# Rows 4 to 10: width 1520 (x=40 to 1560)

# In rows of width 1520:
# Icon at x = 56, width 44, stroke 4
# Title at x = 116 (font-size 30 bold).
# How wide is title?
# Row 1 title: "1 Primary versus data plane:" (28 chars * 18 = 504 px) -> x = 116 to 620.
# Rule text starts at x = 640. Width to 1540 is 900 px.
# At 24px (14.4 px/char), 900 px / 14.4 = 62 chars/line.
# Let's check rule lines:
print("Full width rows (rule width 900 px -> max_chars = 62):")
for i in [0, 1, 3, 4, 5, 6, 7, 8, 9]:
    t, r = rows[i]
    r_lines = wrap_text(r, 62)
    print(f"Row {i+1:2d} ({len(r_lines)} lines):")
    for l in r_lines:
        print(f"   [{len(l):2d}] {l}")

print("\nRow 3 (rule width 510 px -> max_chars = 35):")
t, r = rows[2]
r_lines = wrap_text(r, 35)
print(f"Row 3 ({len(r_lines)} lines):")
for l in r_lines:
    print(f"   [{len(l):2d}] {l}")

sidenote = "hostNetwork pods share the node's IP and port space and skip the CNI; node agents such as kube-proxy, the CNI daemon, node-exporter and the DCGM exporter run this way; check for port conflicts before scheduling"
sn_lines = wrap_text(sidenote, 35)
print(f"\nSide note ({len(sn_lines)} lines):")
for l in sn_lines:
    print(f"   [{len(l):2d}] {l}")

