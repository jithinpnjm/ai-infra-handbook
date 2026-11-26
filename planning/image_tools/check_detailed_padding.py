import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_engine_upgrade.svg")
root = tree.getroot()

boxes = [
    ("Title", 0, 0, 1600, 1200),
    ("L_header", 50, 100, 720, 1060),
    ("L1", 75, 190, 670, 235),
    ("L2", 75, 440, 670, 175),
    ("L3", 75, 630, 670, 160),
    ("L4", 75, 806, 670, 225),
    ("R1", 855, 125, 670, 85),
    ("R2", 855, 238, 670, 105),
    ("R3", 855, 371, 670, 145),
    ("R4", 855, 544, 670, 110),
    ("R_rollback", 855, 682, 670, 110),
    ("R_surge", 855, 804, 670, 336)
]

text_nodes = root.findall('.//{http://www.w3.org/2000/svg}text')

all_pass = True
for idx, t in enumerate(text_nodes):
    bname, bx, by, bw, bh = boxes[idx]
    box_right = bx + bw
    box_bottom = by + bh
    fs = float(t.attrib.get('font-size', '24'))
    ff = t.attrib.get('font-family', 'sans-serif')
    c_w = 0.62 * fs if 'mono' in ff else 0.6 * fs
    
    tspans = t.findall('{http://www.w3.org/2000/svg}tspan')
    if not tspans:
        tx = float(t.attrib.get('x', '0'))
        ty = float(t.attrib.get('y', '0'))
        anchor = t.attrib.get('text-anchor', 'start')
        ttext = t.text.strip()
        twidth = len(ttext) * c_w
        if anchor == 'middle':
            tleft = tx - twidth / 2
            tright = tx + twidth / 2
        else:
            tleft = tx
            tright = tx + twidth
        
        pad_l = tleft - bx
        pad_r = box_right - tright
        pad_t = (ty - fs) - by
        pad_b = box_bottom - ty
        print(f"[{bname}] '{ttext[:30]}...' pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
        if pad_l < 16 or pad_r < 16 or pad_t < 16 or pad_b < 16:
            all_pass = False
            print(f"   WARNING in {bname}!")
    else:
        print(f"[{bname}] ({len(tspans)} lines):")
        cur_y = float(tspans[0].attrib.get('y', '0'))
        for j, ts in enumerate(tspans):
            tx = float(ts.attrib.get('x', '0'))
            if j > 0:
                cur_y += float(ts.attrib.get('dy', '34'))
            ttext = ts.text.strip()
            twidth = len(ttext) * c_w
            tleft = tx
            tright = tx + twidth
            pad_l = tleft - bx
            pad_r = box_right - tright
            pad_t = (cur_y - fs) - by
            pad_b = box_bottom - cur_y
            print(f"   line {j+1}: '{ttext}' (len={len(ttext)}, w={twidth:.1f}) pad_l={pad_l:.1f}, pad_r={pad_r:.1f}")
            if pad_l < 16 or pad_r < 16:
                all_pass = False
                print(f"   WARNING: insufficient horizontal padding! pad_l={pad_l:.1f}, pad_r={pad_r:.1f}")
            if j == 0 and pad_t < 16:
                all_pass = False
                print(f"   WARNING: insufficient top padding! pad_t={pad_t:.1f}")
            if j == len(tspans)-1 and pad_b < 16:
                all_pass = False
                print(f"   WARNING: insufficient bottom padding! pad_b={pad_b:.1f}")

assert all_pass, "Some padding failed!"
print("\nALL BOXES AND LINES HAVE AT LEAST 16px PADDING! (PASSED)")
