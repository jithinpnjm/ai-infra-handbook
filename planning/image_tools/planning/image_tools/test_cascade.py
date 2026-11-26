#!/usr/bin/env python3

def test_full_cascade():
    # Title: y = 46 (dy=0), y = 96 (dy=50) -> bottom = 102
    # Section 1: y = 125, h = 215 (ends at 340)
    # Gap: 40px (380 - 340 = 40)
    # Section 2: y = 380, h = 160 (ends at 540)
    # Gap: 40px (580 - 540 = 40)
    # Section 3: y = 580, h = 220 (ends at 800)
    # Gap: 40px (840 - 800 = 40)
    # Section 4: y = 840, h = 215 (ends at 1055)
    # Gap: 40px (1095 - 1055 = 40)
    # Bottom bar: y = 1095, h = 65 (ends at 1160)
    # Margin bottom: 1200 - 1160 = 40px!

    print("Cascade vertical ranges:")
    print("Title:      46 to 102")
    print("Section 1: 125 to 340 (h=215)")
    print("Section 2: 380 to 540 (h=160)")
    print("Section 3: 580 to 800 (h=220)")
    print("Section 4: 840 to 1055 (h=215)")
    print("Bottom bar: 1095 to 1160 (h=65)")
    print("Bottom margin: 40px")

test_full_cascade()
