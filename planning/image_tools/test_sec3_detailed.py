def check_sec3():
    s3_y = 760
    s3_h = 280
    s3_w = 1520
    
    # 2 rows of cards inside s3:
    # Row 1: y = 818, h = 98 (Top two cards)
    # Gap = 16
    # Row 2: y = 932, h = 98 (Bottom two cards)
    # Check bottom padding of s3: (760 + 280) - (932 + 98) = 1040 - 1030 = 10px (inner container margin)
    
    # Ingress card: 3 lines
    # Can 3 lines fit in h=98?
    # If fs=24:
    # Line 1: baseline = 818 + 16 + 24 = 858
    # Line 2: baseline = 858 + 26 = 884
    # Line 3: baseline = 884 + 26 = 910
    # Bottom pad: (818 + 98) - 910 = 916 - 910 = 6px < 16px!
    print("In h=98, 3 lines of fs=24 has only 6px bottom pad.")

check_sec3()
