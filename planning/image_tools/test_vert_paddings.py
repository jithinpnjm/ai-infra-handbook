import xml.etree.ElementTree as ET

tree = ET.parse("candidate_adapter_pipeline.svg")
root = tree.getroot()

failed = False
groups = root.findall('.//{http://www.w3.org/2000/svg}g')

for g in groups:
    gid = g.attrib.get('id', '')
    rect = g.find('{http://www.w3.org/2000/svg}rect')
    texts = g.findall('{http://www.w3.org/2000/svg}text')
    if rect is not None and texts:
        ry = float(rect.attrib['y'])
        rh = float(rect.attrib['height'])
        
        # find min y - fs and max y
        all_tops = []
        all_bottoms = []
        for text in texts:
            t_fs = float(text.attrib.get('font-size', '24'))
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            if tspans:
                curr_y = float(text.attrib.get('y', '0'))
                for ts in tspans:
                    ts_dy = float(ts.attrib.get('dy', '0'))
                    curr_y += ts_dy
                    ts_fs = float(ts.attrib.get('font-size', t_fs))
                    all_tops.append(curr_y - ts_fs)
                    all_bottoms.append(curr_y)
            else:
                ty = float(text.attrib.get('y', '0'))
                all_tops.append(ty - t_fs)
                all_bottoms.append(ty)
                
        min_top = min(all_tops)
        max_bottom = max(all_bottoms)
        
        top_pad = min_top - ry
        bottom_pad = (ry + rh) - max_bottom
        
        if top_pad < 16 or bottom_pad < 16:
            print(f"[FAIL PAD Y] in {gid}: top={top_pad:.1f}, bottom={bottom_pad:.1f}")
            failed = True
        else:
            print(f"[OK PAD Y] in {gid}: top={top_pad:.1f}, bottom={bottom_pad:.1f}")

assert not failed, "Some vertical paddings failed!"
print("\nALL VERTICAL PADDING CHECKS PASSED!")
