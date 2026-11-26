def test_layout():
    # Right column y bounds: 185 to 1025 (840px total)
    # 7 rows.
    # What if row heights are varied or uniform?
    # Row 1 (4 lines cause): height = 120
    # Row 2 (1 line): height = 95
    # Row 3 (1 line): height = 95
    # Row 4 (1 line): height = 95
    # Row 5 (1 line): height = 95
    # Row 6 (2 lines code, 2 lines cause): height = 110
    # Row 7 (1 line code, 1 line cause): height = 95
    # Total heights = 120 + 95*5 + 110 = 705.
    # Remaining for 6 gaps: 830 - 705 = 125 -> ~20px gap!
    print("Varied heights sum:", 120 + 95*5 + 110, "gaps:", (830 - 705)/6)

test_layout()
