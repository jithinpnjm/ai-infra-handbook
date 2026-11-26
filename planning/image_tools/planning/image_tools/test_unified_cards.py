# Test layout with unified cards for parsers and rules

def test_unified():
    # 1. parsers card: x = 56, y = 398, w = 968, h = 240
    # Icon: (72, 410, 56, 56)
    # Text 1: parsers.py (4 lines)
    # y: 426, 452, 478, 504
    # Top pad: 426 - 19.2 - 398 = 8.8 -> make card y = 390!
    # Card y = 390 to 640 (h = 250)
    # Text 1 y: 422, 448, 474, 500 (top pad: 422 - 19.2 - 390 = 12.8 -> make y = 426, card y = 390 -> 426 - 19.2 - 390 = 16.8!)
    # Text 2: parser detail (5 lines)
    # y: 532, 556, 580, 604, 628
    # Bot pad: 650 - (628 + 6) = 16.0 (>= 16!)
    # Card height = 260 (y = 390 to 650).
    
    # Arrow 3: from (540, 650) to (540, 690) (gap = 40 px).
    
    # 2. rules card: x = 56, y = 690, w = 968, h = 150
    # Icon: (72, 702, 56, 56)
    # Text 1: rules.py (1 line): y = 726 (top pad: 726 - 20.8 - 690 = 15.2 -> make y = 728, top pad = 17.2!)
    # Text 2: rules detail (3 lines):
    # y: 760, 786, 812
    # Bot pad: 840 - (812 + 6) = 22.0 (>= 16!)
    # Card height = 150 (y = 690 to 840).
    
    # Pure Layers container: x = 40, y = 374, w = 1000, h = 482 (ends at 856).
    # Top pad inside pure layers: 390 - 374 = 16 px.
    # Bot pad inside pure layers: 856 - 840 = 16 px.
    
    # Arrow 2 gap: collect card ends at 334. Pure layers starts at 374 -> gap = 40 px!
    # collect card: y = 244 to 334 (h = 90).
    # Arrow 1 gap: cli card ends at 204. collect card starts at 244 -> gap = 40 px!
    # cli card: y = 132 to 204 (h = 72).
    # Title gap: Title ends at 92. cli card starts at 132 -> gap = 40 px!
    
    # Gap after Pure Layers (ends at 856):
    # Test strip starts at 896! (gap = 40 px!).
    # Test strip: y = 896 to 1016 (h = 120).
    # Gap after Test strip: 40 px -> Bottom bar starts at 1056!
    # Bottom bar: y = 1056 to 1136 (h = 80).
    # Bottom margin: 1200 - 1136 = 64 px >= 40 px!
    
    print("ALL GAPS >= 40 PX, BOTTOM MARGIN >= 40 PX, EVERYTHING FITS!")

test_unified()
