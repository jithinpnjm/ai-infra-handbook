import re

col1_items = [
    "why and how things work: the problem each mechanism solves, the range of solutions, how this implementation applies one",
    "BGP peer state: a finite state machine, timers and keepalives; a session must miss its hold timer before routes withdraw, so a failure takes that long to show up",
    "built from protocol specifications, design rationales, real designs and their failures; best captured as flow charts or sequence diagrams",
    "skip them and you get hunt-and-peck troubleshooting from fragments of past incidents"
]

col2_items = [
    "what is normal here: the signal path of each application, the baseline (traffic by time of day, SPF run times, jitter and delay per application, ECMP balance, PFC and ECN rates, temperatures, optic power), the source of truth for configuration, expected convergence time and loss on link failure, security boundaries",
    "write down the normal retransmit rate, latency and load on one leaf switch",
    "radar technician: a DC ohmmeter reads an inductor as a short, so it could not see the inductor failure in parallel with the shorted resistor; every tool has blind spots"
]

col3_items = [
    "accuracy means fit to purpose, not completeness",
    "OSI is good for interfaces and building a stack, poor for what happens where and why",
    "RINA treats error control, flow control and multiplexing as recurring at each scope",
    "different questions need different models: path, control plane, queues, energy and thermal, application protocol"
]

def wrap_text(text, max_chars):
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(' '.join(cur))
    return lines

# Let's inspect Col 2 first since it dictates the maximum height
c2_lines = [wrap_text(it, 29) for it in col2_items]
# Let's see:
# Card 1: 13 lines
# Card 2: 3 lines
# Card 3: 7 lines

# Line height for 24px: 30px
# Let's calculate card heights with top/bottom padding = 18px:
# height = 18 + 24 + (num_lines - 1) * 30 + 18 = 60 + (num_lines - 1) * 30.
# Card 1: 60 + 12 * 30 = 420px.
# Card 2: 60 + 2 * 30 = 120px.
# Card 3: 60 + 6 * 30 = 240px.
# Sum = 780px.
# Gaps: 2 gaps of 16px = 32px.
# Total = 812px.
# If cards start at y = 255:
# Card 1: y = 255 to 675 (h=420)
# Gap = 15
# Card 2: y = 690 to 810 (h=120)
# Gap = 15
# Card 3: y = 825 to 1065 (h=240)
# Total height ends at 1065!
# Column background can end at y = 1075 (bottom padding 10px).
# Bottom bar starts at y = 1095 to 1175 (height 80px).
# Canvas ends at 1200 (bottom margin 25px)!

print("Col 2 layout:")
print("Card 1: 255 to 675 (h=420)")
print("Card 2: 690 to 810 (h=120)")
print("Card 3: 825 to 1065 (h=240)")
print("Bottom of col 2:", 1065)

# Now let's fit Col 1 into the same y = 255 to 1065 space (available height 810px):
c1_lines = [wrap_text(it, 29) for it in col1_items]
# Card 1: 5 lines -> 60 + 4*30 = 180px
# Card 2: 6 lines -> 60 + 5*30 = 210px
# Card 3: 6 lines -> 60 + 5*30 = 210px
# Card 4: 4 lines -> 60 + 3*30 = 150px
# Sum = 750px.
# 3 gaps of (810 - 750) / 3 = 60 / 3 = 20px!
# Perfect match! Exactly 810px!
print("\nCol 1 layout:")
y = 255
for i, l in enumerate(c1_lines):
    h = 60 + (len(l) - 1) * 30
    print(f"Card {i+1}: y={y} to {y+h} (h={h})")
    y += h + 20

# Now let's fit Col 3 into the same space:
c3_lines = [wrap_text(it, 29) for it in col3_items]
# Card 1: 2 lines -> 60 + 1*30 = 90px
# Card 2: 4 lines -> 60 + 3*30 = 150px
# Card 3: 3 lines -> 60 + 2*30 = 120px
# Card 4: 5 lines -> 60 + 4*30 = 180px
# Sum = 540px.
# If we expand padding on Col 3 or add spacing:
# Available = 810px. 810 - 540 = 270px extra.
# We can increase vertical padding of cards in Col 3, e.g. padding top/bottom = 35px:
# 60 + 34 = 94px base. 4 cards * 34px = 136px extra.
# Or gaps = 40px, or both!
# Let's see: base height 540px. With 3 gaps of 35px = 105px -> 645px.
# Or give each card in Col 3 a bit more breathing room (e.g. h = 110, 180, 150, 210 = 650px).
