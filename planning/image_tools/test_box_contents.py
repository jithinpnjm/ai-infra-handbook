# Check text positions inside each box

# Box 1: Shared Nodes (y=150, h=54)
# What is inside Shared Nodes?
# 4 nodes:
# Col 1: c1 (10.10.0.11)
# Col 2: br0 (10.10.0.1/24)
# Col 3: c2 (10.10.0.12)
# Col 4: uplink NIC
# Node icon (outline) + text label (24px bold)
# Let's check text y baseline: 150 + 35 = 185.
# Top padding = 185 - 24 - 150 = 11px font cap -> 150 to 161 = 11px.
# Wait, can Shared Nodes box be h=60?
# If shared_nodes_y = 145, h = 60, bottom = 205.
# Gap to lane1 = 40px -> lane1_y = 245.

# Let's check Lane 1 (y=245..440, h=195):
# Title: 'c1 to c2 on the same bridge' (30px bold)
# Title y baseline = 245 + 32 = 277.
# Desc line 1: y = 277 + 28 = 305
# Desc line 2: y = 305 + 26 = 331
# Desc line 3: y = 331 + 26 = 357
# Note line 1: y = 357 + 28 = 385
# Note line 2: y = 385 + 26 = 411
# Bottom padding = 440 - (411 + 6) = 23px (>= 16px!).
# Top padding = (277 - 30) - 245 = 2px cap -> wait, let's adjust baselines!

def check_box(name, y_top, y_bottom, lines_spec):
    # lines_spec: list of (size, dy)
    curr_y = y_top
    print(f"\n--- {name} (y={y_top}..{y_bottom}, h={y_bottom - y_top}) ---")
    first = True
    for size, gap in lines_spec:
        if first:
            curr_y += gap
            first = False
        else:
            curr_y += gap
        top_cap = curr_y - size * 0.8
        bot_desc = curr_y + size * 0.2
        print(f"  Line size={size}, baseline={curr_y:.1f}, top_cap={top_cap:.1f}, bot={bot_desc:.1f}")
    top_pad = lines_spec[0][1] - lines_spec[0][0]*0.8
    bot_pad = y_bottom - bot_desc
    print(f"  Top padding: {top_pad:.1f}px, Bottom padding: {bot_pad:.1f}px")
    assert top_pad >= 16, f"Top pad {top_pad} < 16"
    assert bot_pad >= 16, f"Bot pad {bot_pad} < 16"

# Let's test Lane 1 with proper padding:
# h=195: top_pad=20 -> first baseline = y_top + 20 + 30*0.8 = y_top + 44.
