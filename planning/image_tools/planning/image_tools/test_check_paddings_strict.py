import xml.etree.ElementTree as ET

def check_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # We check each text element
    # Map of text content to enclosing box bounds (x, y, w, h)
    boxes = {
        "which value is used": (40, 110, 740, 350), # title beside icon
        "ansible-inventory --host": (60, 196, 410, 52),
        "debug var": (486, 196, 274, 52),
        "-vvv": (60, 260, 338, 52),
        "grep": (414, 260, 346, 52),
        "extra vars with -e sit at the top of the stack and role vars/ also beats inventory": (60, 324, 700, 116),
        "type": (820, 110, 740, 350),
        "var | type_debug shows str, int, bool, list, dict": (840, 210, 700, 210),
        "render template": (40, 500, 740, 350),
        "ansible localhost -m template with -e @vars.yml": (60, 586, 700, 114),
        "inspect /tmp/out": (60, 720, 700, 96),
        "condition": (820, 500, 740, 350),
        "debug msg of the when expression": (840, 586, 700, 104),
        "-vv false_condition": (840, 710, 700, 106),
        "gpu_count 8 from -e is a number, from a CSV it is the text 8 and the when comparison fails": (40, 890, 1520, 120),
    }

    all_ok = True
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = " ".join("".join(elem.itertext()).split())
        fs = float(elem.attrib['font-size'])
        if full_text in ["1", "2", "3", "4", "Checking which variable value is used"]:
            continue
            
        box = boxes.get(full_text)
        if not box:
            print(f"WARNING: No box mapped for '{full_text}'")
            continue
            
        bx, by, bw, bh = box
        # check each visual line
        tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
        if not tspans:
            lines = [(full_text, elem.attrib.get('font-family', 'sans-serif'))]
        else:
            lines = []
            for tsp in tspans:
                txt = tsp.text.strip()
                ff = tsp.attrib.get('font-family', elem.attrib.get('font-family', 'sans-serif'))
                lines.append((txt, ff))
                
        for line_txt, ff in lines:
            is_mono = 'mono' in ff
            mult = 0.62 if is_mono else 0.60
            w = len(line_txt) * fs * mult
            pad_h = (bw - w) / 2 # if centered
            print(f"Line '{line_txt}' fs={fs} ff={ff}: est_w={w:.1f}px, box_w={bw}px -> horiz padding = {pad_h:.1f}px")
            if pad_h < 16:
                print(f"  FAIL: pad_h {pad_h:.1f} < 16!")
                all_ok = False
            else:
                print(f"  PASS: pad_h >= 16")

    assert all_ok, "Some paddings failed!"
    print("\nALL PADDING CHECKS PASSED!")

check_paddings("test_candidate_val.svg")
