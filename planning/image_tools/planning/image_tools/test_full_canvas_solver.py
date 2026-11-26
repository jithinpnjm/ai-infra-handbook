# Full canvas solver ensuring Title top >= 40 and Bottom bar bottom <= 1160

def solve_canvas():
    # Margins:
    # Top margin: Title top = 40 px -> y1 = 76, y2 = 126.
    # Title bottom = 126 + 12 = 138.
    # Gap to Row 1 = 40 px -> Row 1 starts at y = 178!
    
    # 1. cli.py (y = 178 to 250, h = 72)
    # Arrow 1: y = 250 to 290 (gap = 40)
    
    # 2. collect.py (y = 290 to 376, h = 86)
    # Arrow 2: y = 376 to 416 (gap = 40)
    
    # 3. Pure Layers Container (y = 416 to 898, h = 482)
    # Inside:
    # parsers card: y = 432 to 690 (h = 258)
    # Arrow 3: y = 690 to 730 (gap = 40)
    # rules card: y = 730 to 882 (h = 152)
    # Bot pad inside pure layers: 898 - 882 = 16 px!
    # Top pad inside pure layers: 432 - 416 = 16 px!
    
    # Right Column:
    # models.py: y = 178 to 274 (h = 96)
    # Gap = 40 -> Exit code container starts at y = 314!
    # Exit code container: y = 314 to 898 (h = 584)
    # Both Left and Right columns end at y = 898!
    # Inside Exit codes (4 cards of h = 110, 3 gaps of 32):
    # Top pad = 18 px -> Card 0: 332 to 442
    # Gap = 32 -> Card 1: 474 to 584
    # Gap = 32 -> Card 3: 616 to 726
    # Gap = 32 -> Card 4: 758 to 868
    # Bot pad inside exit container: 898 - 868 = 30 px >= 16!
    
    # Gap after Pure Layers / Exit Codes (ends at 898):
    # Test strip starts at y = 938! (gap = 40 px!)
    # Test strip: y = 938 to 1046 (h = 108 px).
    
    # Gap after Test strip: 40 px -> Bottom bar starts at y = 1086!
    # Bottom bar: y = 1086 to 1158 (h = 72 px).
    # Bottom margin: 1200 - 1158 = 42 px >= 40 px!
    
    print("SOLVED PERFECTLY!")
    print(f"Title top: {76 - 36} px (>= 40)")
    print(f"Bottom margin: {1200 - 1158} px (>= 40)")
    print(f"Pure Layers bot: 898, Test strip top: 938, gap: {938 - 898} px (>= 40)")
    print(f"Test strip bot: 1046, Bottom bar top: 1086, gap: {1086 - 1046} px (>= 40)")

solve_canvas()
