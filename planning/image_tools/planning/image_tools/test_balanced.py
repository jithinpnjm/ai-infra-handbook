#!/usr/bin/env python3

def test_balanced_cascade():
    # Title: y = 46 to 102
    # Section 1: y = 125, h = 200 (ends at 325)
    # Gap: 40px
    # Section 2: y = 365, h = 210 (ends at 575)
    # Gap: 40px
    # Section 3: y = 615, h = 205 (ends at 820)
    # Gap: 40px
    # Section 4: y = 860, h = 195 (ends at 1055)
    # Gap: 40px
    # Bottom bar: y = 1095, h = 65 (ends at 1160)
    # Bottom margin: 40px (1200 - 1160 = 40)
    
    print("Balanced Cascade:")
    print("Section 1: 125 to 325 (h=200)")
    print("Section 2: 365 to 575 (h=210)")
    print("Section 3: 615 to 820 (h=205)")
    print("Section 4: 860 to 1055 (h=195)")
    print("Bottom bar: 1095 to 1160 (h=65)")

test_balanced_cascade()
