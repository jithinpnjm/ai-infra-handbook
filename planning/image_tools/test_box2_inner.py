#!/usr/bin/env python3

def test_box2_inner():
    # Box 2 outer: y = 95 to 335 (h = 240)
    # Circle & icon at y = 110..166
    # Inner card: y = 175, h = 145 (ends at 320)
    # Card top = 175, bottom = 320
    
    # We have 4 lines in total:
    # L1: "2 perf script report"
    # L2: "flamegraph (perf 5.8 and newer)"
    # L3: "perf script,"
    # L4: "stackcollapse-perf.pl, flamegraph.pl"
    
    # Font size = 24. Cap height ~ 18px. Baseline y means top of letters is y - 18, bottom is y + 6.
    # If lines at:
    # y1 = 208 -> top = 190 (padding from 175 is 15px -> let's make y1 = 212 and card top = 172: 212-18 = 194, 194-172 = 22px!)
    # y2 = 238 -> bottom = 244
    # y3 = 274 -> top = 256
    # y4 = 304 -> bottom = 310 (card bottom = 328: 328 - 310 = 18px!)
    
    # Outer box: y = 90, h = 250 (ends at 340).
    # Inner card: y = 170, w = 550, h = 160 (ends at 330).
    
    card_top = 170
    card_bottom = 330
    
    y1, y2, y3, y4 = 208, 238, 274, 304
    
    pad_top = (y1 - 18) - card_top
    pad_bottom = card_bottom - (y4 + 6)
    
    print(f"Inner card pad_top: {pad_top}px (>= 16)")
    print(f"Inner card pad_bottom: {pad_bottom}px (>= 16)")
    assert pad_top >= 16
    assert pad_bottom >= 16
    print("PASS!")

test_box2_inner()
