import xml.etree.ElementTree as ET

tree = ET.parse("candidate_retry.svg")
root = tree.getroot()

boxes = [
    # (name, box_x, box_y, box_w, box_h, text_str)
    ("Title", 0, 0, 1600, 100, "Retry layers multiply"),
    ("Retries card", 445, 358, 215, 100, "retries on its own"),
    ("Rule Bar", 40, 1030, 1520, 130, "set the budget at the gateway"),
    ("Arithmetic panel title", 720, 110, 840, 85, "Arithmetic panel"),
    ("Card 1 (Formula)", 760, 205, 760, 195, "One client, k attempts"),
    ("Card 2 (SRE)", 760, 440, 760, 135, "SRE chapter"),
    ("Card 3 (AWS)", 760, 615, 760, 135, "AWS builders article"),
    ("Card 4 (1,024)", 760, 790, 760, 85, "With 4 attempts"),
    ("Layer 1 (SDK)", 70, 150, 330, 95, "SDK"),
    ("Layer 2 (gateway)", 70, 290, 330, 95, "gateway"),
    ("Layer 3 (mesh sidecar)", 70, 430, 330, 95, "mesh sidecar"),
    ("Layer 4 (router)", 70, 570, 330, 95, "router"),
    ("Layer 5 (and sometimes more)", 70, 710, 330, 95, "(and sometimes more)"),
]

print("=== CHECKING TEXT PADDINGS (rule: >= 16px horizontal and vertical) ===")

all_pass = True

for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    txt = " ".join("".join(elem.itertext()).split())
    fs = float(elem.attrib['font-size'])
    anchor = elem.attrib.get('text-anchor', 'start')
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        lines = []
        for tsp in tspans:
            lines.append((tsp.text.strip(), float(tsp.attrib.get('font-size', fs)), float(tsp.attrib.get('dy', 0))))
    else:
        lines = [(elem.text.strip(), fs, 0)]
        
    # Match box
    matched_box = None
    for b in boxes:
        if b[5] and b[5] in txt:
            matched_box = b
            break
            
    assert matched_box is not None, f"Could not match box for text: '{txt}'"
    b_name, bx, by, bw, bh, _ = matched_box
    
    print(f"\n--- Checking '{txt[:35]}...' in '{b_name}' (w={bw}, h={bh}) ---")
    
    # Calculate vertical extent
    # Baseline of first line is y
    first_y = y
    # Ascent ~ 0.75 * fs, descent ~ 0.25 * fs
    line_y = y
    top_extent = y - 0.75 * lines[0][1]
    
    for i, (l_str, l_fs, l_dy) in enumerate(lines):
        line_y += l_dy
        w_est = len(l_str) * 0.6 * l_fs
        
        # Horizontal padding
        if anchor == 'middle':
            pad_left = (x - w_est / 2) - bx
            pad_right = (bx + bw) - (x + w_est / 2)
        else:
            pad_left = x - bx
            pad_right = (bx + bw) - (x + w_est)
            
        print(f"  Line {i+1}: '{l_str}'")
        print(f"    width={w_est:.1f}px, pad_left={pad_left:.1f}px, pad_right={pad_right:.1f}px")
        if min(pad_left, pad_right) < 16:
            print(f"    ERROR: horizontal padding < 16px! (got {min(pad_left, pad_right):.1f})")
            all_pass = False
            
    bottom_extent = line_y + 0.25 * lines[-1][1]
    pad_top = top_extent - by
    pad_bottom = (by + bh) - bottom_extent
    print(f"  Vertical: top_extent={top_extent:.1f}, bottom_extent={bottom_extent:.1f}")
    print(f"  Vertical padding: pad_top={pad_top:.1f}px, pad_bottom={pad_bottom:.1f}px")
    if min(pad_top, pad_bottom) < 16:
        print(f"  ERROR: vertical padding < 16px! (got {min(pad_top, pad_bottom):.1f})")
        all_pass = False

assert all_pass, "Some text failed the padding check!"
print("\n>>> ALL TEXT PADDINGS EXCEED 16px! (PASS) <<<")
