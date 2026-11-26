import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate.svg")
root = tree.getroot()

# Check text inside cards:
# Card 1: x in [50, 760], y in [105, 595]
# Card 2: x in [840, 1550], y in [105, 595]
# Card 3: x in [840, 1550], y in [655, 1145]
# Card 4: x in [50, 760], y in [655, 1145]

# Let's inspect each <tspan> in each card
cards = [
    ("Card 1", "stage-1", 50, 760, 105, 595),
    ("Card 2", "stage-2", 840, 1550, 105, 595),
    ("Card 3", "stage-3", 840, 1550, 655, 1145),
    ("Card 4", "side-game-day", 50, 760, 655, 1145),
]

for card_name, g_id, x_min, x_max, y_min, y_max in cards:
    g = root.find(f".//*[@id='{g_id}']")
    text_elem = g.findall('{http://www.w3.org/2000/svg}text')[-1] # the body text
    
    cur_y = 0
    cur_x = 0
    print(f"\nChecking {card_name} (bounds x=[{x_min}, {x_max}], y=[{y_min}, {y_max}]):")
    
    for tsp in text_elem.iter('{http://www.w3.org/2000/svg}tspan'):
        # Check if it has direct text or children
        txt = "".join(tsp.itertext()).strip()
        if not txt:
            continue
        
        # Determine position
        if 'x' in tsp.attrib:
            cur_x = float(tsp.attrib['x'])
        if 'y' in tsp.attrib:
            cur_y = float(tsp.attrib['y'])
        elif 'dy' in tsp.attrib:
            cur_y += float(tsp.attrib['dy'])
            
        fs = float(tsp.attrib.get('font-size', text_elem.attrib.get('font-size', 24)))
        is_mono = (tsp.attrib.get('font-family') == 'monospace')
        char_w = (0.62 if is_mono else 0.6) * fs
        w = len(txt) * char_w
        
        x_left = cur_x
        x_right = cur_x + w
        y_top = cur_y - fs
        y_bottom = cur_y + 4 # baseline descender approx
        
        pad_left = x_left - x_min
        pad_right = x_max - x_right
        pad_top = y_top - y_min
        pad_bottom = y_max - y_bottom
        
        # print(f"  [{fs:2.0f}px] '{txt[:30]:30s}' -> x=[{x_left:5.1f}, {x_right:5.1f}] pad_L={pad_left:4.1f} pad_R={pad_right:4.1f} pad_T={pad_top:4.1f} pad_B={pad_bottom:4.1f}")
        assert pad_left >= 16, f"Left padding violated: {pad_left} < 16 for '{txt}'"
        assert pad_right >= 16, f"Right padding violated: {pad_right} < 16 for '{txt}'"
        assert pad_top >= 16, f"Top padding violated: {pad_top} < 16 for '{txt}'"
        assert pad_bottom >= 16, f"Bottom padding violated: {pad_bottom} < 16 for '{txt}'"

print("\nALL TEXT LINES HAVE AT LEAST 16px PADDING FROM BOX EDGES!")
