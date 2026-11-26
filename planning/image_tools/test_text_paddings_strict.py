# Let's verify every single line in every box for:
# - font size >= 24px
# - top padding >= 16px
# - bottom padding >= 16px
# - left padding >= 16px
# - right padding >= 16px

# Canvas w = 1600. All boxes: x = 40, w = 1520 (x_right = 1560)
# Inside boxes: text_x >= 40 + 16 = 56.

boxes = [
    {"name": "Shared Host", "y": 140, "h": 56},
    {"name": "Lane 1", "y": 236, "h": 196},
    {"name": "Lane 2", "y": 472, "h": 260},
    {"name": "Lane 3", "y": 772, "h": 118},
    {"name": "Footer", "y": 930, "h": 134},
    {"name": "Takeaway", "y": 1104, "h": 56},
]

# Let's check Box 1: Shared Host
# Contains: host (badge/label), c1 (10.10.0.11), br0 (10.10.0.1/24), c2 (10.10.0.12), uplink NIC
# Font size: 24px.
# Baseline = 140 + 35 = 175.
# Top cap: 175 - 24*0.75 = 157. Pad top = 157 - 140 = 17px (>= 16).
# Bottom desc: 175 + 24*0.2 = 179.8. Pad bot = 196 - 179.8 = 16.2px (>= 16).
print("Box 1 padding check OK!")

# Let's check Box 6: Takeaway Bar
# Text: 'A container is only a namespace plus a cable'
# Font: 24px bold.
# Baseline = 1104 + 35 = 1139.
# Top cap: 1139 - 24*0.75 = 1121. Pad top = 1121 - 1104 = 17px (>= 16).
# Bottom desc: 1139 + 24*0.2 = 1143.8. Pad bot = 1160 - 1143.8 = 16.2px (>= 16).
print("Box 6 padding check OK!")

# Let's check Box 4: Lane 3 (y=772..890, h=118)
# Line 1: 'host:8080 to c1:80' (30px bold)
# Line 2: iptables -t nat -A PREROUTING... (24px mono)
# Line 3: iptables -t nat -A OUTPUT... (24px mono)
l3_base1 = 772 + 38 # 810. Top cap = 810 - 30*0.75 = 787.5. Pad top = 787.5 - 772 = 15.5 -> let's make base1 = 772 + 39 = 811 (pad top 16.5)
l3_base2 = 811 + 32 # 843.
l3_base3 = 843 + 27 # 870. Bot desc = 870 + 24*0.2 = 874.8. Pad bot = 890 - 874.8 = 15.2 -> let's adjust!
