#!/usr/bin/env python3

def opt_table():
    # We want table to fit between y=165 and y=1055 (available height = 890px)
    # 7 rows + 1 optional card = 8 items
    # 7 gaps of 10px = 70px
    # Available item height = 890 - 70 = 820px
    
    # Let's test different column widths:
    # Threat card: x=825, w=275
    # Control card: x=1115, w=420
    # Inside RP (x=800..1560, w=760)
    print("Testing table wrapping and heights...")

opt_table()
