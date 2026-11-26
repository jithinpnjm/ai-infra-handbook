import xml.etree.ElementTree as ET

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# Let's map each text/tspan line to its enclosing box width
# Box widths:
# Left col boxes (cli, collect, parsers, rules):
# Box width = 860. Icon occupies left side up to x=118.
# Text starts at x=136. Right edge of box = 900.
# Usable width from x=136 to x=900 is 764px.
# Exit code container: width = 620. Text starts at x=965. Right edge = 1560. Usable width = 595px.
# models.py: width = 620. Icon up to x=1014. Text starts at x=1030. Right edge = 1560. Usable width = 530px.
# parser_detail: width = 620. Text starts at x=965. Right edge = 1560. Usable width = 595px.
# rules_detail: width = 620. Text starts at x=965. Right edge = 1560. Usable width = 595px.
# test_strip: width = 1520. Icon up to x=116. Text starts at x=136. Right edge = 1560. Usable width = 1424px.
# bottom_bar: width = 1520. Centered text at x=800.

# Let's inspect every tspan and calculate padding to box edge:
print("Checking paddings for all text elements...")
all_ok = True

for text_elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(text_elem.attrib.get('font-size', 24))
    tspans = list(text_elem.iter('{http://www.w3.org/2000/svg}tspan'))
    
    # If no tspans, check text directly
    if not tspans:
        content = "".join(text_elem.itertext()).strip()
        # check width
        ff = text_elem.attrib.get('font-family', 'sans')
        is_mono = 'mono' in ff
        mult = 0.62 if is_mono else 0.60
        est_w = len(content) * fs * mult
        print(f"Direct text: '{content[:40]}...' fs={fs} est_w={est_w:.1f}")
    else:
        # Check by visual lines (tspans that start a new line via dy!=0 or distinct lines)
        # Group tspans by lines:
        lines = []
        curr_line = []
        for tsp in tspans:
            dy = tsp.attrib.get('dy', '0')
            x = tsp.attrib.get('x')
            txt = tsp.text or ""
            t_fs = float(tsp.attrib.get('font-size', fs))
            t_ff = tsp.attrib.get('font-family', text_elem.attrib.get('font-family', 'sans'))
            is_mono = 'mono' in t_ff
            if (dy != '0' or x is not None) and curr_line and dy != '0':
                lines.append(curr_line)
                curr_line = [(txt, t_fs, is_mono)]
            else:
                curr_line.append((txt, t_fs, is_mono))
        if curr_line:
            lines.append(curr_line)
            
        for line_items in lines:
            line_w = sum(len(txt) * tfs * (0.62 if mono else 0.60) for txt, tfs, mono in line_items)
            line_txt = "".join(txt for txt, tfs, mono in line_items)
            print(f"  Line: '{line_txt[:45]:45s}' -> w={line_w:5.1f}px")

print("\nAll lines printed.")
