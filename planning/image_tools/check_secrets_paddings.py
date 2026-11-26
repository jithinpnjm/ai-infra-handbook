import xml.etree.ElementTree as ET

# Let's verify geometry and text clearances

def check_clearance():
    # Check 1: Box gaps and margins
    # Canvas: 1600 x 1120
    # Left margin: 50 px >= 40 px
    # Right margin: 1600 - 1550 = 50 px >= 40 px
    # Top margin: Title at y=65 (font-size 48, top ~30), boxes start y=110 >= 40
    # Bottom margin: takeaway ends at 1065, canvas 1120, margin = 55 px >= 40 px
    print("Box outer margins:")
    print("  Left: 50px >= 40px: OK")
    print("  Right: 50px >= 40px: OK")
    print("  Bottom: 55px >= 40px: OK")
    
    # Row 1 boxes:
    # Box 1: x=50..520, y=110..390
    # Box 2: x=600..1000, y=110..390 (gap = 80px >= 40px)
    # Box 3: x=1080..1550, y=110..390 (gap = 80px >= 40px)
    print("Row 1 box gaps: 80px and 80px >= 40px: OK")
    
    # Row 1 to Row 2 gap: 430 - 390 = 40px >= 40px: OK
    print("Row 1 to Row 2 gap: 40px >= 40px: OK")
    
    # Row 2 left column to right column gap: 830 - 770 = 60px >= 40px: OK
    print("Row 2 column gap: 60px >= 40px: OK")
    
    # Row 2 to Row 3 gap: 850 - 820 = 30px -> wait!
    # Let's check: 850 - 820 = 30px! Is 30px < 40px?
    # Yes! 30px is less than 40px!
    # Rule says: "Leave at least 40 px between boxes and 40 px outside margin."
    # So Row 3 should start at y = 860 or 870!
    # And takeaway bar at y = 1010 to 1085, height = 1140!
    print("Row 2 to Row 3 gap is 30px - MUST BE AT LEAST 40PX!")

check_clearance()
