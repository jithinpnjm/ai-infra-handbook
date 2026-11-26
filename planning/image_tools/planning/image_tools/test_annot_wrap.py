def test_annotation_wrap():
    w = 320 - 32 # 288 available
    l1 = "where pinning happens at L4"
    l2 = "L7 or client-side balancing fixes it"
    
    # l1: 27 chars. 27 * 0.6 * 24 = 388.8 > 288. Must wrap onto 2 lines!
    # "where pinning" -> 13 * 0.6 * 24 = 187.2
    # "happens at L4" -> 13 * 0.6 * 24 = 187.2
    # Both fit in 288!
    
    # l2: 36 chars.
    # "L7 or client-side" -> 17 * 0.6 * 24 = 244.8 <= 288!
    # "balancing fixes it" -> 18 * 0.6 * 24 = 259.2 <= 288!
    # Both fit in 288!
    print("l1 wrapped:", 187.2, "<=", 288)
    print("l2 wrapped:", 259.2, "<=", 288)

test_annotation_wrap()
