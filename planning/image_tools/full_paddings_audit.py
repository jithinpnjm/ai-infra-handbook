import xml.etree.ElementTree as ET

tree = ET.parse("candidate_ca.svg")
root = tree.getroot()

cards = [
    ("scale-up-step-1", 65, 178, 690, 120),
    ("scale-up-step-2", 65, 320, 690, 120),
    ("scale-up-step-3", 65, 462, 690, 174),
    ("scale-up-step-4", 65, 658, 690, 124),
    ("scale-up-step-5", 65, 804, 690, 96),
    ("scale-down-condition-box", 845, 178, 690, 178),
    ("blocker-1", 862, 434, 656, 58),
    ("blocker-2", 862, 498, 656, 58),
    ("blocker-3", 862, 562, 656, 58),
    ("blocker-4", 862, 626, 656, 58),
    ("blocker-5-orange", 862, 690, 656, 114),
    ("blocker-6", 862, 810, 656, 86),
    ("limits-card", 65, 1030, 690, 114),
    ("gpu-card", 845, 1030, 690, 114)
]

for gid, rx, ry, rw, rh in cards:
    g = root.find(f".//*[@id='{gid}']")
    assert g is not None, f"Missing group {gid}"
    text_el = g.find('{http://www.w3.org/2000/svg}text')
    assert text_el is not None, f"Missing text in {gid}"
    
    fs = float(text_el.attrib['font-size'])
    tx = float(text_el.attrib['x'])
    ty = float(text_el.attrib['y'])
    
    tspans = text_el.findall('{http://www.w3.org/2000/svg}tspan')
    
    print(f"\n--- Checking {gid} ---")
    print(f"Rect: x={rx}..{rx+rw}, y={ry}..{ry+rh}")
    
    pad_top = (ty - fs * 0.8) - ry
    print(f"pad_top: {pad_top:.1f} px")
    assert pad_top >= 16.0, f"In {gid}: pad_top {pad_top} < 16!"
    
    curr_y = ty
    max_line_right = 0
    min_line_left = tx
    
    if tspans:
        # Group tspans by line (dy != 0 starts new line)
        line_texts = []
        cur_line = []
        cur_tx = tx
        for i, ts in enumerate(tspans):
            t_dy = float(ts.attrib.get('dy', '0'))
            t_x_attr = ts.attrib.get('x')
            if i > 0 and (t_dy > 0 or t_x_attr is not None):
                line_texts.append((cur_tx, cur_line))
                cur_line = []
                if t_x_attr is not None:
                    cur_tx = float(t_x_attr)
                curr_y += t_dy
            cur_line.append((ts.text or "", ts.attrib.get('font-family') == 'monospace' or text_el.attrib.get('font-family') == 'monospace'))
        if cur_line:
            line_texts.append((cur_tx, cur_line))
            
        for line_x, segments in line_texts:
            line_w = sum(len(txt) * (0.62 if is_m else 0.60) * fs for txt, is_m in segments)
            line_right = line_x + line_w
            if line_right > max_line_right:
                max_line_right = line_right
            if line_x < min_line_left:
                min_line_left = line_x
    else:
        txt = text_el.text or ""
        is_mono = text_el.attrib.get('font-family') == 'monospace'
        coeff = 0.62 if is_mono else 0.60
        line_w = len(txt) * coeff * fs
        max_line_right = tx + line_w
        min_line_left = tx
        
    pad_bottom = (ry + rh) - (curr_y + fs * 0.2)
    pad_right = (rx + rw) - max_line_right
    pad_left = min_line_left - rx
    
    print(f"pad_bottom: {pad_bottom:.1f} px")
    print(f"pad_left:   {pad_left:.1f} px")
    print(f"pad_right:  {pad_right:.1f} px")
    
    assert pad_bottom >= 16.0, f"In {gid}: pad_bottom {pad_bottom} < 16!"
    assert pad_left >= 16.0, f"In {gid}: pad_left {pad_left} < 16!"
    assert pad_right >= 16.0, f"In {gid}: pad_right {pad_right} < 16!"
    print(f"[{gid}] ALL PADDINGS >= 16 px (PASS)")

print("\nEVERY SINGLE CARD STRICTLY SATISFIES PADDING >= 16 PX ON ALL 4 SIDES!")
