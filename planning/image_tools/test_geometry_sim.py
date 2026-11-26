import re
import xml.etree.ElementTree as ET

# Define the coordinates
# Title: When a Service fails, confirm in order (48px bold)
# Canvas: 1600 x 1200

# Arrow on left:
# x = 65, y1 = 140, y2 = 1064
# Arrow text: x = 85, y = 570..630

# Rungs:
# Rung 1: x=160, y=140, w=990, h=92
# Small Box: x=1190, y=140, w=370, h=92
# Rung 2: x=160, y=274, w=1400, h=92
# Rung 3: x=160, y=408, w=1400, h=92
# Rung 4: x=160, y=542, w=780, h=120
# Orange Callout: x=980, y=542, w=580, h=120
# Rung 5: x=160, y=704, w=1400, h=92
# Rung 6: x=160, y=838, w=1400, h=92
# Rung 7: x=160, y=972, w=1400, h=92
# Takeaway: x=40, y=1104, w=1520, h=56

boxes = [
    ("Rung 1", 160, 140, 990, 92),
    ("Small Box", 1190, 140, 370, 92),
    ("Rung 2", 160, 274, 1400, 92),
    ("Rung 3", 160, 408, 1400, 92),
    ("Rung 4", 160, 542, 780, 120),
    ("Orange Callout", 980, 542, 580, 120),
    ("Rung 5", 160, 704, 1400, 92),
    ("Rung 6", 160, 838, 1400, 92),
    ("Rung 7", 160, 972, 1400, 92),
    ("Takeaway", 40, 1104, 1520, 56)
]

print("1. Checking margins >= 40px:")
for name, bx, by, bw, bh in boxes:
    ml = bx
    mr = 1600 - (bx + bw)
    mt = by
    mb = 1200 - (by + bh)
    assert ml >= 40, f"{name} margin left {ml} < 40"
    assert mr >= 40, f"{name} margin right {mr} < 40"
    assert mt >= 40, f"{name} margin top {mt} < 40"
    assert mb >= 40, f"{name} margin bottom {mb} < 40"
    print(f"  OK {name}: ml={ml}, mr={mr}, mt={mt}, mb={mb}")

print("\n2. Checking pairwise box overlap and gaps:")
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        n1, x1, y1, w1, h1 = boxes[i]
        n2, x2, y2, w2, h2 = boxes[j]
        # check if disjoint
        x_overlap = not (x1 + w1 <= x2 or x2 + w2 <= x1)
        y_overlap = not (y1 + h1 <= y2 or y2 + h2 <= y1)
        assert not (x_overlap and y_overlap), f"Overlap between {n1} and {n2}!"
        
        # If they overlap in x, check vertical gap >= 40
        if x_overlap:
            if y1 + h1 <= y2:
                gap = y2 - (y1 + h1)
                assert gap >= 40, f"Vertical gap between {n1} and {n2} is {gap} < 40"
            elif y2 + h2 <= y1:
                gap = y1 - (y2 + h2)
                assert gap >= 40, f"Vertical gap between {n2} and {n1} is {gap} < 40"
                
        # If they overlap in y, check horizontal gap >= 40
        if y_overlap:
            if x1 + w1 <= x2:
                gap = x2 - (x1 + w1)
                assert gap >= 40, f"Horizontal gap between {n1} and {n2} is {gap} < 40"
            elif x2 + w2 <= x1:
                gap = x1 - (x2 + w2)
                assert gap >= 40, f"Horizontal gap between {n2} and {n1} is {gap} < 40"

print("All margins and pairwise box gaps are >= 40px!")
