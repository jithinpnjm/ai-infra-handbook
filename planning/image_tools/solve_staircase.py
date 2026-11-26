# Let's test a complete layout solver!

def check_disjoint_with_gap(b1, b2, gap=40):
    # b = (x1, y1, x2, y2)
    sep_x = (b2[0] - b1[2] >= gap) or (b1[0] - b2[2] >= gap)
    sep_y = (b2[1] - b1[3] >= gap) or (b1[1] - b2[3] >= gap)
    return sep_x or sep_y

# Test case:
b1 = (100, 500, 260, 600)
b2 = (200, 360, 360, 460)
print("b1 and b2 separated by >= 40?", check_disjoint_with_gap(b1, b2, 40))
# b1.top - b2.bottom = 500 - 460 = 40!
