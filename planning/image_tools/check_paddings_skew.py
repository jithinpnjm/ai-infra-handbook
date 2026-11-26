import xml.etree.ElementTree as ET

# We need to verify that every line of text inside its box has at least 16px padding on:
# - Left
# - Right
# - Top
# - Bottom

# Let's inspect each card and text:
# Card 1:
# Outer: x=50, y=150, w=730, h=425 (right=780, bottom=575)
# Title: Engine version against router (30px bold, font multiplier 0.6)
# Title length: 29 chars * 30 * 0.6 = 522px
# Title x: 156, y: 214. Right = 156 + 522 = 678.
# Card 1 outer right: 780. Right padding = 780 - 678 = 102px >= 16px!
# Icon: from (78, 178) to (134, 234). Title x=156. Icon right to title left = 156 - 134 = 22px >= 16px!
# Title baseline: 214. Top of font is ~214 - 23 = 191. Card top = 150. Top padding = 41px >= 16px!
# Inner box 1: x=74, y=260, w=682, h=285 (right=756, bottom=545)
# Title bottom to inner box top: 260 - 220 = 40px gap!

# Inner box 1 lines:
# Line 1: 'Request accepted by the old version and' (39 chars * 24 * 0.6 = 561.6px)
# x=100. Right = 100 + 561.6 = 661.6. Box right = 756. Right padding = 756 - 661.6 = 94.4px >= 16px! Left padding = 100 - 74 = 26px >= 16px!
# y=315. Top of font = 315 - 18 = 297. Box top = 260. Top padding = 297 - 260 = 37px >= 16px!
# Line 2: 'rejected by the new in the same minute: two' (43 chars * 24 * 0.6 = 619.2px)
# x=100. Right = 100 + 619.2 = 719.2. Box right = 756. Right padding = 36.8px >= 16px!
# Line 3: 'versions run at once during a rollout' (37 chars * 24 * 0.6 = 532.8px)
# x=100. Right = 100 + 532.8 = 632.8. Right padding = 123.2px >= 16px!
# y = 315 + 42 + 42 = 399. Bottom of font = 399 + 6 = 405. Box bottom = 545. Bottom padding = 545 - 405 = 140px >= 16px!

print("Card 1 paddings verified!")

# Card 2 (Prefix cache):
# Outer: x=820, y=150, w=730, h=425 (right=1550, bottom=575)
# Title tspan: Prefix cache: (14 chars * 30 * 0.6 = 252px)
# Title x: 926, y: 214. Right = 926 + 252 = 1178. Card right = 1550. Right padding = 372px >= 16px!
# Icon 2: (848, 178) to (904, 234). Title x=926. Clearance = 926 - 904 = 22px >= 16px!
# Inner box 2: x=844, y=260, w=682, h=285 (right=1526, bottom=545)
# Left padding: 870 - 844 = 26px >= 16px!
# Lines of Card 2:
c2_lines = [
    'different weights produce different KV values;',
    'reusing a block from old weights would feed',
    'the new model numbers it never computed,',
    'wrong answers with no error; key the prefix',
    'cache and cache-aware routing by model version',
    'so no hit crosses a version boundary'
]
y_start = 302
for i, l in enumerate(c2_lines):
    w = len(l) * 24 * 0.6
    r = 870 + w
    r_pad = 1526 - r
    y = y_start + i * 34
    top_pad = (y - 18) - 260 if i == 0 else 0
    bot_pad = 545 - (y + 6) if i == len(c2_lines) - 1 else 0
    print(f"C2 Line {i+1}: len={len(l)}, w={w:.1f}, r_pad={r_pad:.1f}, y={y}")
    assert r_pad >= 16, f"C2 Line {i+1} right padding {r_pad} < 16"
print("Top pad:", (y_start - 18) - 260)
print("Bottom pad:", 545 - (y_start + (len(c2_lines)-1)*34 + 6))
assert (y_start - 18) - 260 >= 16
assert 545 - (y_start + (len(c2_lines)-1)*34 + 6) >= 16
print("Card 2 paddings verified!")

# Card 3 (Tokenizer against weights):
# Outer: x=50, y=615, w=730, h=425 (right=780, bottom=1040)
# Title: Tokenizer against weights: (27 chars * 30 * 0.6 = 486px)
# Title x: 156, y: 679. Right = 156 + 486 = 642. Card right = 780. Right padding = 138px >= 16px!
# Icon 3: (78, 643) to (134, 699). Title x=156. Clearance = 156 - 134 = 22px >= 16px!
# Inner box 3: x=74, y=725, w=682, h=285 (right=756, bottom=1010)
# Left padding: 100 - 74 = 26px >= 16px!
c3_lines = [
    'a checkpoint with the wrong tokenizer fails',
    'quietly, garbage output and green',
    'infrastructure; the registry record makes',
    'weights, tokenizer and config one object',
    'with one version'
]
y_start = 770
for i, l in enumerate(c3_lines):
    w = len(l) * 24 * 0.6
    r = 100 + w
    r_pad = 756 - r
    y = y_start + i * 38
    print(f"C3 Line {i+1}: len={len(l)}, w={w:.1f}, r_pad={r_pad:.1f}, y={y}")
    assert r_pad >= 16, f"C3 Line {i+1} right padding {r_pad} < 16"
print("Top pad:", (y_start - 18) - 725)
print("Bottom pad:", 1010 - (y_start + (len(c3_lines)-1)*38 + 6))
assert (y_start - 18) - 725 >= 16
assert 1010 - (y_start + (len(c3_lines)-1)*38 + 6) >= 16
print("Card 3 paddings verified!")

# Card 4 (Client-facing):
# Outer: x=820, y=615, w=730, h=425 (right=1550, bottom=1040)
# Title: Client-facing: (15 chars * 30 * 0.6 = 270px)
# Title x: 926, y: 679. Right = 926 + 270 = 1196. Card right = 1550. Right padding = 354px >= 16px!
# Icon 4: (848, 643) to (904, 699). Title x=926. Clearance = 926 - 904 = 22px >= 16px!
# Inner box 4: x=844, y=725, w=682, h=285 (right=1526, bottom=1010)
# Left padding: 870 - 844 = 26px >= 16px!
c4_lines = [
    'a user who sees both versions in one',
    'conversation may see style change midway;',
    'sticky routing by tenant or session during',
    'the canary sends one user back to the same',
    'version every time; this is the difference',
    'between a canary and an A/B test'
]
y_start = 768
for i, l in enumerate(c4_lines):
    w = len(l) * 24 * 0.6
    r = 870 + w
    r_pad = 1526 - r
    y = y_start + i * 36
    print(f"C4 Line {i+1}: len={len(l)}, w={w:.1f}, r_pad={r_pad:.1f}, y={y}")
    assert r_pad >= 16, f"C4 Line {i+1} right padding {r_pad} < 16"
print("Top pad:", (y_start - 18) - 725)
print("Bottom pad:", 1010 - (y_start + (len(c4_lines)-1)*36 + 6))
assert (y_start - 18) - 725 >= 16
assert 1010 - (y_start + (len(c4_lines)-1)*36 + 6) >= 16
print("Card 4 paddings verified!")

# Takeaway bar:
# Box: x=50, y=1075, w=1500, h=90 (right=1550, bottom=1165)
# Line 1: 'pin tokenizer, weights and config as one version, key caches by version,' (71 chars * 24 * 0.6 = 1022.4px)
# Center x=800. Half width = 511.2px. Left = 800 - 511.2 = 288.8. Right = 800 + 511.2 = 1311.2.
# Left padding: 288.8 - 50 = 238.8px >= 16px!
# Right padding: 1550 - 1311.2 = 238.8px >= 16px!
# y1 = 1113. Top of font = 1113 - 18 = 1095. Top padding = 1095 - 1075 = 20px >= 16px!
# Line 2: 'keep a session on one version during a canary' (45 chars * 24 * 0.6 = 648px)
# Left = 800 - 324 = 476. Right = 800 + 324 = 1124. Padding = 426px >= 16px!
# y2 = 1113 + 34 = 1147. Bottom of font = 1147 + 6 = 1153. Bottom padding = 1165 - 1153 = 12px? Wait!
# 1165 - 1153 = 12px < 16px!
print("BOTTOM PAD TAKEAWAY:", 1165 - 1153)
