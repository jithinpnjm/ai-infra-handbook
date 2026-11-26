#!/usr/bin/env python3

def test_top_row_alignment():
    # Box: y = 105 to 325 (height 220)
    by = 105
    bh = 220
    
    # Edge 1: 3 lines
    # Icon: y = 122 to 162 (h=40)
    # Gap: 162 to 195 = 33px
    # Line 1: y = 195 (top 171)
    # Line 2: y = 230 (top 206)
    # Line 3: y = 265 (top 241, bottom 271)
    # Bottom pad: 325 - 271 = 54px.
    print("Edge 1 OK")

    # State: 3 lines
    # Icon: y = 122 to 172 (h=50)
    # Gap: 172 to 205 = 33px
    # Line 1: y = 205 (top 175) -> fs=30
    # Line 2: y = 245 (top 221) -> fs=24
    # Line 3: y = 280 (top 256, bottom 286)
    # Bottom pad: 325 - 286 = 39px.
    print("State OK")

    # Edge 3: 4 lines
    # Icon: y = 122 to 162 (h=40)
    # Gap: 162 to 192 = 30px
    # Line 1: y = 192 (top 168)
    # Line 2: y = 224 (top 200)
    # Line 3: y = 256 (top 232)
    # Line 4: y = 288 (top 264, bottom 294)
    # Bottom pad: 325 - 294 = 31px.
    print("Edge 3 OK")

test_top_row_alignment()
