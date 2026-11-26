def check_disjoint(b1, b2, name1, name2, min_gap=40):
    # b = (x1, y1, x2, y2)
    # They are disjoint with gap if either x gap >= min_gap or y gap >= min_gap
    dx = max(0, max(b1[0] - b2[2], b2[0] - b1[2]))
    dy = max(0, max(b1[1] - b2[3], b2[1] - b1[3]))
    
    # Check if they intersect
    intersect_x = not (b1[2] <= b2[0] or b1[0] >= b2[2])
    intersect_y = not (b1[3] <= b2[1] or b1[1] >= b2[3])
    overlap = intersect_x and intersect_y
    if overlap:
        print(f"OVERLAP between {name1} and {name2}!")
        return False
    
    # Gap is either dx or dy
    gap = max(dx, dy)
    print(f"[{name1}] and [{name2}]: gap = {gap}px (dx={dx}, dy={dy})")
    assert gap >= min_gap, f"Gap between {name1} and {name2} is {gap} < {min_gap}!"
    return True

# Step 1: x=50..210, y=660..780
# Diamond 1: cx=240, cy=490, w=110, h=76 -> x=185..295, y=452..528
# Step 2: x=270..430, y=580..700
s1 = (50, 660, 210, 780)
d1 = (185, 452, 295, 528)
s2 = (270, 580, 430, 700)

check_disjoint(s1, d1, "Step 1", "Diamond 1", 40)
check_disjoint(s2, d1, "Step 2", "Diamond 1", 40)
check_disjoint(s1, s2, "Step 1", "Step 2", 40)
print("All pairwise checks passed with >= 40px gap!")
