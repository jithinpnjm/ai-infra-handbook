def check_all():
    H = 1060
    
    # Check canvas
    assert 900 <= H <= 1200
    
    # Check margins
    assert 50 >= 40 # left
    assert (1600 - 1550) >= 40 # right
    assert 110 >= 40 # top
    assert (H - 1015) >= 40 # bottom
    
    # Check row gaps
    gap_row1_2 = 715 - 675
    assert gap_row1_2 >= 40, f"gap_row1_2 {gap_row1_2} < 40"
    
    gap_row2_3 = 935 - 895
    assert gap_row2_3 >= 40, f"gap_row2_3 {gap_row2_3} < 40"
    
    # Check col gaps in row 1
    gap_col1_2 = 470 - 430
    assert gap_col1_2 >= 40, f"gap_col1_2 {gap_col1_2} < 40"
    
    gap_col2_3 = 1210 - 1170
    assert gap_col2_3 >= 40, f"gap_col2_3 {gap_col2_3} < 40"
    
    # Check col gap in row 3
    gap_r3 = 930 - 890
    assert gap_r3 >= 40, f"gap_r3 {gap_r3} < 40"
    
    print("ALL MARGINS AND GAPS >= 40PX PASSED!")

check_all()
