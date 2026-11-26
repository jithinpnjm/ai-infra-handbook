# Let's compute exact y positions for H=1080 or H=1050

# Y budget:
# y = 55: Title text-anchor="middle" font-size="48" font-weight="bold"

# Row 1: Gates (Latency & Quality)
# y = 100, height = 120
# y lines for gate_latency (2 lines, dy=34): y=152, 186
# y lines for gate_quality (3 lines, dy=32): y=142, 174, 206
# Icon at y=132 (56x56) -> centered in 120px box (top padding (120-56)/2 = 32px)

# Gap: 20px -> y = 240
# Row 2: Rule 1 (Hard failures rollback) [ORANGE HIGHLIGHT]
# 4 lines of text: y = 275, 307, 339, 371
# Height = 160 px (from y=240 to 400).
# Icon at y=292 (56x56) -> centered in 160px box (top padding (160-56)/2 = 52px)

# Gap: 15px -> y = 415
# Row 3: Rule 2 (Below minimum requests hold)
# 1 line of text: y = 458
# Height = 75 px (from y=415 to 490).
# Icon at y=425 (56x56) -> top padding 9px

# Gap: 15px -> y = 505
# Row 4: Rule 3 (Soft signals hold)
# 2 lines of text: y = 545, 577
# Height = 100 px (from y=505 to 605).
# Icon at y=527 (56x56) -> top padding 22px

# Gap: 15px -> y = 620
# Row 5: Rule 4 (Otherwise promote)
# 1 line of text: y = 663
# Height = 75 px (from y=620 to 695).
# Icon at y=630 (56x56) -> top padding 9px

# Gap: 20px -> y = 715
# Row 6: Operational rules (two cards side by side, w=730 each)
# Card 1 (Prefix cache, 4 lines): text at y = 750, 782, 814, 846
# Card 2 (Router weights, 3 lines): text at y = 766, 798, 830
# Height = 160 px (from y=715 to 875).
# Icon at y=767 (56x56) -> top padding 52px

# Gap: 20px -> y = 895
# Row 7: Takeaway bar / Reasons (full width 1500)
# 2 lines of text: y = 942, 974
# Height = 110 px (from y=895 to 1005).
# Icon at y=922 (56x56) -> top padding 27px

# Bottom margin: from y=1005 to 1050 -> 45px!
# Total height H = 1050!
print("Total height H = 1050 is completely harmonious and clean!")
