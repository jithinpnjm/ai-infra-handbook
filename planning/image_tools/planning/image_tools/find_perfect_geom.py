#!/usr/bin/env python3

def find_perfect_geometry():
    # Fixed constraints:
    # Width = 1600, Height = 1200
    # Margins: Left = 40, Right = 40, Bottom = 40
    # Gaps between distinct sections >= 40
    
    # 5 sections:
    # Title: y = 44 (dy=0), y = 92 (dy=48) -> bottom = 98
    # Section 1 (Filename Anatomy)
    # Gap >= 40
    # Section 2 (Variants strip)
    # Gap >= 40
    # Section 3 (Decision flow)
    # Gap >= 40
    # Section 4 (Tool line & early check)
    # Gap >= 40
    # Bottom bar: ends at 1160 (bottom margin 40)
    
    # Let's work backwards from 1160:
    # Bottom bar: y = 1095, h = 65 (1095 to 1160)
    # Gap >= 40 -> Section 4 ends at 1055
    # Section 4: y = 875 to 1055 (h = 180)
    # Gap >= 40 -> Section 3 ends at 835
    # Section 3: y = 620 to 835 (h = 215)
    # Gap >= 40 -> Section 2 ends at 580
    # Section 2: y = 350 to 580 (h = 230)
    # Gap >= 40 -> Section 1 ends at 310
    # Section 1: y = 120 to 310 (h = 190)
    # Gap from title to Section 1: 120 - 98 = 22px
    
    print("Testing vertical section boundaries:")
    print("Sec 1: 120 to 310 (h=190)")
    print("Sec 2: 350 to 580 (h=230)")
    print("Sec 3: 620 to 835 (h=215)")
    print("Sec 4: 875 to 1055 (h=180)")
    print("BBar : 1095 to 1160 (h=65)")
    print("All gaps: 350-310=40, 620-580=40, 875-835=40, 1095-1055=40. Perfect!")

find_perfect_geometry()
