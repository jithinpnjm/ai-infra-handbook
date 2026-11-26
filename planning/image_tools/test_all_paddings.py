def check():
    # Card inner boxes:
    # y = 260 to 545 (height 285) for row 1
    # y = 725 to 1010 (height 285) for row 2
    # Left inner box x = 74 to 756 (w = 682)
    # Right inner box x = 844 to 1526 (w = 682)

    # C1 (3 lines):
    c1_y = [320, 360, 400]
    for i, y in enumerate(c1_y):
        top = y - 18
        bot = y + 6
        if i == 0:
            assert top - 260 >= 16, f"C1 top pad {top - 260} < 16"
        if i == len(c1_y) - 1:
            assert 545 - bot >= 16, f"C1 bot pad {545 - bot} < 16"
    print("C1 vertical pad OK")

    # C2 (7 lines):
    c2_y = [296 + i * 34 for i in range(7)]
    assert (c2_y[0] - 18) - 260 >= 16, f"C2 top pad {(c2_y[0] - 18) - 260} < 16"
    assert 545 - (c2_y[-1] + 6) >= 16, f"C2 bot pad {545 - (c2_y[-1] + 6)} < 16"
    print("C2 vertical pad OK")

    # C3 (5 lines):
    c3_y = [765 + i * 38 for i in range(5)]
    assert (c3_y[0] - 18) - 725 >= 16, f"C3 top pad {(c3_y[0] - 18) - 725} < 16"
    assert 1010 - (c3_y[-1] + 6) >= 16, f"C3 bot pad {1010 - (c3_y[-1] + 6)} < 16"
    print("C3 vertical pad OK")

    # C4 (6 lines):
    c4_y = [765 + i * 36 for i in range(6)]
    assert (c4_y[0] - 18) - 725 >= 16, f"C4 top pad {(c4_y[0] - 18) - 725} < 16"
    assert 1010 - (c4_y[-1] + 6) >= 16, f"C4 bot pad {1010 - (c4_y[-1] + 6)} < 16"
    print("C4 vertical pad OK")

    # Takeaway bar:
    # Box: x = 50, y = 1065, w = 1500, h = 100 (bottom = 1165)
    # y1 = 1104, y2 = 1140
    assert (1104 - 18) - 1065 >= 16, "Takeaway top pad < 16"
    assert 1165 - (1140 + 6) >= 16, "Takeaway bot pad < 16"
    print("Takeaway vertical pad OK")

check()
