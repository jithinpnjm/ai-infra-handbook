import xml.etree.ElementTree as ET

# Define the visual boxes
boxes = [
    # (name, x, y, w, h)
    ("Actor 1 Box", 60, 110, 420, 230),
    ("Actor 2 Box", 560, 110, 460, 230),
    ("Outcome Box", 180, 690, 700, 92),
    ("Fix 1 Card", 1080, 130, 460, 195),
    ("Fix 2 Card", 1080, 345, 460, 195),
    ("Fix 3 Card", 1080, 560, 460, 215),
    ("Related 1 Card", 65, 845, 470, 285),
    ("Related 2 Card", 565, 845, 470, 285),
    ("Related 3 Card", 1065, 845, 470, 285),
]

# Check box margins (>= 40px between distinct functional groups, >= 40 outside margin)
for name, x, y, w, h in boxes:
    assert x >= 40, f"{name} outside margin left < 40: {x}"
    assert x + w <= 1560, f"{name} outside margin right < 40: {x + w}"
    assert y >= 40, f"{name} outside margin top < 40: {y}"
    assert y + h <= 1160, f"{name} outside margin bottom < 40: {y + h}"

print("All boxes pass margin checks!")

# Parse SVG and check text elements inside each box
tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# Check each text line in each box
for text_el in root.iter('{http://www.w3.org/2000/svg}text'):
    x_base = float(text_el.attrib.get('x', 0))
    y_base = float(text_el.attrib.get('y', 0))
    fs_base = float(text_el.attrib.get('font-size', 24))
    anchor = text_el.attrib.get('text-anchor', 'start')
    
    tspans = list(text_el.iter('{http://www.w3.org/2000/svg}tspan'))
    if not tspans:
        # Single line
        content = text_el.text.strip()
        is_mono = "monospace" in text_el.attrib.get('font-family', '')
        char_factor = 0.62 if is_mono else 0.60
        text_w = len(content) * fs_base * char_factor
        if anchor == 'middle':
            t_left = x_base - text_w / 2
            t_right = x_base + text_w / 2
        else:
            t_left = x_base
            t_right = x_base + text_w
        t_top = y_base - fs_base * 0.8
        t_bottom = y_base + fs_base * 0.2
        print(f"Text '{content}': left={t_left:.1f}, right={t_right:.1f}, top={t_top:.1f}, bottom={t_bottom:.1f}")
    else:
        cur_y = y_base
        for tsp in tspans:
            content = (tsp.text or "").strip()
            x = float(tsp.attrib.get('x', x_base))
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            fs = float(tsp.attrib.get('font-size', fs_base))
            is_mono = "monospace" in tsp.attrib.get('font-family', '') or "monospace" in text_el.attrib.get('font-family', '')
            char_factor = 0.62 if is_mono else 0.60
            text_w = len(content) * fs * char_factor
            if anchor == 'middle':
                t_left = x - text_w / 2
                t_right = x + text_w / 2
            else:
                t_left = x
                t_right = x + text_w
            t_top = cur_y - fs * 0.8
            t_bottom = cur_y + fs * 0.2
            print(f"  tspan '{content}': left={t_left:.1f}, right={t_right:.1f}, top={t_top:.1f}, bottom={t_bottom:.1f}")

