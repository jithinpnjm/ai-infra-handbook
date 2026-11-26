# Let's test 3 columns with exact bounding box padding calculations.
# Canvas: 1600 x 1200

# Top Title: y = 52, fs = 48
# Pre-step banner: y = 80..155 (h = 75)
# Bottom bar: y = 1135..1185 (h = 50)
# Group containers: y = 175..1115 (h = 940)
# Group headers: y = 175..230 (h = 55)
# Step slots in Col 2 & 3: from y = 240 to 1105 = 865px.
# 5 cards: 865 / 5 = 173px per slot.
# If card height = 156px, gap = 17px.
# Card 1: y = 240..396
# Card 2: y = 413..569
# Card 3: y = 586..742
# Card 4: y = 759..915
# Card 5: y = 932..1088

# Inside a card of h = 156:
# Text bounding box:
# Top margin: y_first_baseline - 0.75 * fs >= 16
# Bottom margin: h - (y_last_baseline + 0.25 * fs) >= 16

# For fs=24: ascender ~ 18px, descender ~ 6px.
# For fs=30: ascender ~ 22px, descender ~ 7px.

def check_card_vertical_fit(card_h, lines):
    # lines is list of (fs, dy_from_prev)
    # first line dy is relative to top of card
    # We want to find best first_y such that:
    # top_pad = first_y - ascender >= 16
    # bot_pad = card_h - (last_y + descender) >= 16
    
    # Let's compute min height needed:
    total_dy = sum(dy for _, dy in lines[1:])
    ascender_first = 0.75 * lines[0][0]
    descender_last = 0.25 * lines[-1][0]
    min_h = 16 + ascender_first + total_dy + descender_last + 16
    return min_h

# Let's check max lines in Col 2 & 3:
# Step 3:
# L1 (30px): '3 Retransmissions'
# L2 (30px): 'and loss:'
# L3 (24px): 'tc qdisc add dev veth1 root'
# L4 (24px): 'netem loss 2%, compare'
# L5 (24px): 'with 0% loss'
lines_s3 = [(30, 0), (30, 30), (24, 26), (24, 24), (24, 24)]
min_h_s3 = check_card_vertical_fit(156, lines_s3)
print(f"Step 3 min_h needed: {min_h_s3:.1f}px (vs card_h 156)")
