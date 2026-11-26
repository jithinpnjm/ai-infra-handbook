import xml.etree.ElementTree as ET

def check_paddings(svg_path):
    print(f"=== Checking paddings and text fit for {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Map text elements to their containing boxes or bounding areas
    # For each text line: (line_text, x, y, font_size, font_family, box_tuple, icon_tuple)
    # box_tuple: (bx, by, bw, bh)
    # icon_tuple: (ix, iy, iw, ih) or None
    
    # We will inspect all text elements directly from the SVG
    all_ok = True
    
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = " ".join("".join(elem.itertext()).split())
        fs = float(elem.attrib['font-size'])
        ff = elem.attrib.get('font-family', 'sans-serif')
        is_mono = 'mono' in ff
        factor = 0.62 if is_mono else 0.60
        anchor = elem.attrib.get('text-anchor', 'start')
        
        tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            lines = []
            for tsp in tspans:
                lines.append((tsp.text.strip(), float(tsp.attrib.get('x', elem.attrib.get('x', 0))), float(tsp.attrib.get('dy', 0))))
        else:
            lines = [(elem.text.strip(), float(elem.attrib.get('x', 0)), 0.0)]
            
        base_y = float(elem.attrib.get('y', 0))
        
        # Calculate width of each line
        for line_txt, lx, dy in lines:
            w = len(line_txt) * fs * factor
            if anchor == 'middle':
                x_left = lx - w / 2.0
                x_right = lx + w / 2.0
            elif anchor == 'end':
                x_left = lx - w
                x_right = lx
            else:
                x_left = lx
                x_right = lx + w
                
            print(f"Text: '{line_txt[:40]}' fs={fs} ff={ff}: est_w={w:.1f}px, left={x_left:.1f}, right={x_right:.1f}")
            
            # Check canvas margins (must fit inside 1600 canvas with 40px margin: left >= 40, right <= 1560)
            if x_left < 39.9:
                print(f"  ERROR: x_left {x_left} < 40!")
                all_ok = False
            if x_right > 1560.1:
                print(f"  ERROR: x_right {x_right} > 1560!")
                all_ok = False
                
    assert all_ok, "Some text lines violated canvas margins!"
    print("\nALL TEXT LINES FIT WELL INSIDE 1600px CANVAS WITH >= 40px MARGIN!")

if __name__ == "__main__":
    check_paddings("test_candidate_meminfo.svg")
