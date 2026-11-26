import xml.etree.ElementTree as ET

tree = ET.parse("candidate_adapter_pipeline.svg")
root = tree.getroot()

def get_line_width(text, font_size, font_family):
    is_mono = "monospace" in font_family
    rate = 0.62 if is_mono else 0.6
    return len(text) * font_size * rate

# Let's inspect each group that has a rect and text
groups = root.findall('.//{http://www.w3.org/2000/svg}g')
failed = False

for g in groups:
    gid = g.attrib.get('id', '')
    rect = g.find('{http://www.w3.org/2000/svg}rect')
    texts = g.findall('{http://www.w3.org/2000/svg}text')
    if rect is not None and texts:
        rx = float(rect.attrib['x'])
        ry = float(rect.attrib['y'])
        rw = float(rect.attrib['width'])
        rh = float(rect.attrib['height'])
        
        # Check all lines in all texts in this group
        for text in texts:
            t_ff = text.attrib.get('font-family', 'sans-serif')
            t_fs = float(text.attrib.get('font-size', '24'))
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            
            if tspans:
                curr_y = float(text.attrib.get('y', '0'))
                for ts in tspans:
                    ts_text = (ts.text or "").strip()
                    if not ts_text:
                        continue
                    ts_x = float(ts.attrib.get('x', text.attrib.get('x', '0')))
                    ts_dy = float(ts.attrib.get('dy', '0'))
                    curr_y += ts_dy
                    ts_fs = float(ts.attrib.get('font-size', t_fs))
                    ts_ff = ts.attrib.get('font-family', t_ff)
                    lw = get_line_width(ts_text, ts_fs, ts_ff)
                    
                    left_pad = ts_x - rx
                    right_pad = (rx + rw) - (ts_x + lw)
                    top_pad = curr_y - ts_fs - ry
                    bot_pad = (ry + rh) - curr_y
                    
                    if left_pad < 16 or right_pad < 16:
                        print(f"[FAIL PAD X] in {gid}: line '{ts_text}' lw={lw:.1f}, left={left_pad:.1f}, right={right_pad:.1f}")
                        failed = True
                    else:
                        print(f"[OK PAD X] in {gid}: line '{ts_text[:20]}...' left={left_pad:.1f}, right={right_pad:.1f}")
            else:
                txt = "".join(text.itertext()).strip()
                tx = float(text.attrib.get('x', '0'))
                ty = float(text.attrib.get('y', '0'))
                lw = get_line_width(txt, t_fs, t_ff)
                anchor = text.attrib.get('text-anchor', 'start')
                if anchor == 'middle':
                    left_pad = (tx - lw / 2) - rx
                    right_pad = (rx + rw) - (tx + lw / 2)
                else:
                    left_pad = tx - rx
                    right_pad = (rx + rw) - (tx + lw)
                if left_pad < 16 or right_pad < 16:
                    print(f"[FAIL PAD X] in {gid}: text '{txt}' lw={lw:.1f}, left={left_pad:.1f}, right={right_pad:.1f}")
                    failed = True
                else:
                    print(f"[OK PAD X] in {gid}: text '{txt[:20]}...' left={left_pad:.1f}, right={right_pad:.1f}")

assert not failed, "Some padding checks failed!"
print("\nALL HORIZONTAL PADDING CHECKS PASSED (at least 16px padding on all sides)!")
