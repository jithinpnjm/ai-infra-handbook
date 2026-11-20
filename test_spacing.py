H = 1200
boxes = [
    ("hosts", 105, 185),
    ("card1", 225, 415),
    ("card2", 455, 675),
    ("card3", 715, 935),
    ("card4", 975, 1155),
]

for i in range(len(boxes) - 1):
    b1 = boxes[i]
    b2 = boxes[i+1]
    gap = b2[1] - b1[2]
    print(f"Gap between {b1[0]} and {b2[0]}: {gap} px")
    assert gap >= 40, f"Gap {gap} < 40!"

bottom_margin = H - boxes[-1][2]
print(f"Bottom margin: {bottom_margin} px")
assert bottom_margin >= 40

left_margin = 60
right_margin = 1600 - 1540
print(f"Left margin: {left_margin} px, Right margin: {right_margin} px")
assert left_margin >= 40 and right_margin >= 40

print("ALL SPACING AND MARGIN RULES SATISFIED!")
