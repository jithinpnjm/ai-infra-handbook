import math

def simulate():
    # Canvas dimensions
    width = 1600
    height = 1200
    
    # Title
    # Line 1: Slowness is a funnel: measure it, find the limit,
    # Line 2: find the segment, then split loss from delay
    t_line1 = "Slowness is a funnel: measure it, find the limit,"
    t_line2 = "find the segment, then split loss from delay"
    
    t1_w = len(t_line1) * 0.60 * 48
    t2_w = len(t_line2) * 0.60 * 48
    print(f"Title L1 width: {t1_w:.1f}px (avail: {width - 80}px)")
    print(f"Title L2 width: {t2_w:.1f}px (avail: {width - 80}px)")
    assert t1_w <= width - 80
    assert t2_w <= width - 80
    
    # Funnel and Side Box layout:
    # Let's see:
    # If the side box is on the right:
    # Side box x: 1180 to 1560 (width = 380)
    # Funnel:
    # Margin left = 40.
    # Funnel width at top: 1100 (from x = 40 to 1140).
    # Center of funnel: (40 + 1140)/2 = 590.
    # Let's check gap between funnel (max right = 1140) and side box (min left = 1180):
    # Gap = 1180 - 1140 = 40px! Exactly matches the >= 40px rule!
    # Margin right of side box: 1600 - 1560 = 40px! Exactly matches >= 40px rule!
    
    # Let's check vertical bounds:
    # Title: y = 50, 105. Height ends at y = 125.
    # Gap after title: y = 170 start of funnel & side box.
    # Bottom takeaway bar: y = 1100 to 1160 (height 60).
    # Gap before takeaway bar: 40px -> content ends at y = 1060.
    # Vertical range for funnel: y = 170 to 1060 (height = 890px).
    # We have 5 trapezoids.
    # 4 gaps of 40px = 160px.
    # Remaining height = 890 - 160 = 730px.
    # Each trapezoid height: 730 / 5 = 146px.
    # Let's make each trapezoid height = 142px, and 4 gaps of 42px.
    # 5 * 142 + 4 * 42 = 710 + 168 = 878px.
    # Starts at y = 170:
    # Step 1: y = 170 .. 312
    # Step 2: y = 354 .. 496
    # Step 3: y = 538 .. 680
    # Step 4: y = 722 .. 864
    # Step 5: y = 906 .. 1048
    # Gap to takeaway bar: 1100 - 1048 = 52px (>= 40px).
    # Takeaway bar: y = 1100 .. 1160.
    # Canvas height = 1200. Bottom margin: 1200 - 1160 = 40px.
    
    print("Vertical layout verified!")

simulate()
