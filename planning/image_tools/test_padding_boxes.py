# Test box paddings and margins

boxes = [
    ("Top Box", 100, 160, 960, 145),
    ("Pending Box", 150, 350, 860, 90),
    ("Container Branches", 50, 485, 1060, 590),
    ("Branch 1", 75, 515, 310, 185),
    ("Sub-box", 75, 745, 310, 115),
    ("Suspect", 75, 905, 310, 145),
    ("Branch 2", 425, 515, 310, 185),
    ("Branch 3", 775, 515, 310, 185),
    ("ResourceQuota", 1150, 485, 400, 590),
]

# Check outside margins (all >= 40px)
for name, x, y, w, h in boxes:
    left_m = x
    right_m = 1600 - (x + w)
    top_m = y
    bot_m = 1140 - (y + h)
    if name in ["Container Branches", "Top Box", "Pending Box", "ResourceQuota"]:
        assert left_m >= 40, f"{name} left margin {left_m} < 40"
        assert right_m >= 40, f"{name} right margin {right_m} < 40"
        assert top_m >= 40, f"{name} top margin {top_m} < 40"
        assert bot_m >= 40, f"{name} bottom margin {bot_m} < 40"
        print(f"Margin PASS: {name} (L={left_m}, R={right_m}, T={top_m}, B={bot_m})")

# Check gaps between boxes
gaps = [
    ("Top Box to Pending Box", 350 - (160 + 145)), # 45px
    ("Pending Box to Container", 485 - (350 + 90)), # 45px
    ("Branch 1 to Branch 2", 425 - (75 + 310)), # 40px
    ("Branch 2 to Branch 3", 775 - (425 + 310)), # 40px
    ("Branch 1 to Sub-box", 745 - (515 + 185)), # 45px
    ("Sub-box to Suspect", 905 - (745 + 115)), # 45px
    ("Container to ResourceQuota", 1150 - (50 + 1060)), # 40px
]

for name, gap in gaps:
    assert gap >= 40, f"Gap {name} {gap} < 40"
    print(f"Gap PASS: {name} = {gap}px")

print("\nALL MARGINS AND GAPS >= 40px!")
