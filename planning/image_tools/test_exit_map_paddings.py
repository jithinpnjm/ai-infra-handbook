import xml.etree.ElementTree as ET

def check_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    boxes = {
        "Exit codes tell you what happened, from 0 for success to 128 plus N for a signal": (40, 20, 1520, 140),
        "0": (40, 175, 135, 80),
        "1": (215, 175, 230, 80), # inside its column / track
        "2": (485, 175, 192, 80),
        "126": (717, 175, 180, 80),
        "127": (937, 175, 165, 80),
        "128 + N": (1142, 175, 198, 80),
        "255": (1380, 175, 180, 80),
        "Success": (40, 320, 135, 530),
        "General error. For grep, diff and cmp: no match or files differ, not an error": (215, 320, 230, 530),
        "Misuse of a command, or a real error for grep and diff": (485, 320, 192, 530),
        "Found but not executable": (717, 320, 180, 530),
        "Command not found": (937, 320, 165, 530),
        "130 Ctrl-C": (1158, 440, 166, 60),
        "137 SIGKILL": (1158, 525, 166, 60),
        "143 SIGTERM": (1158, 610, 166, 60),
        "Status out of range, or ssh connection failure": (1380, 320, 180, 530),
        "Read the code, then check which program produced it.": (40, 890, 1520, 66)
    }

    all_ok = True
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = " ".join("".join(elem.itertext()).split())
        fs = float(elem.attrib['font-size'])
        box = boxes.get(full_text)
        if not box:
            print(f"WARNING: No box mapped for '{full_text}'")
            continue
        bx, by, bw, bh = box

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
            pad_h = (bw - w) / 2 # since text-anchor="middle"
            print(f"Line '{line_txt}' fs={fs} est_w={w:.1f}px, box_w={bw}px -> pad_h={pad_h:.1f}px")
            if pad_h < 16:
                print(f"  FAIL: pad_h {pad_h:.1f} < 16!")
                all_ok = False
            else:
                print(f"  PASS: pad_h >= 16")

    assert all_ok, "Some paddings failed!"
    print("\nALL PADDING CHECKS PASSED!")

check_paddings("test_exit_map.svg")
