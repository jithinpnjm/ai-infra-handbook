import xml.etree.ElementTree as ET

def check_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # Map each label to its enclosing box (x, y, w, h)
    boxes = {
        "Reading hosts.ini: hosts, groups, groups of groups": (0, 0, 1600, 100),
        "[gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12": (60, 116, 630, 124),
        "a group collects hosts that share a role": (60, 250, 700, 56),
        "each host has a name and optionally an address": (60, 316, 700, 90),
        "[login] login01 ansible_host=10.0.10.5": (60, 416, 700, 90),
        "[cluster:children] gpu login": (60, 516, 700, 90),
        "[cluster:vars] ansible_user=automation, ansible_python_interpreter=/usr/bin/python3": (60, 616, 700, 124),
        "cluster": (1050, 130, 280, 70),
        "ansible_user and interpreter apply to all three machines": (910, 240, 560, 90),
        "gpu": (860, 420, 260, 190),
        "login": (1260, 420, 260, 190),
        "a group of groups, written with :children, lets one command reach every member: a play aimed at cluster reaches all three machines": (40, 780, 1520, 90),
        "ansible-inventory --graph (run first: shows the nesting at a glance), --list, --host gpu01": (40, 890, 1520, 75),
        "a node missing from the inventory quietly misses every change you make": (40, 985, 1520, 75),
        "The inventory is the phone book of your fleet": (40, 1080, 1520, 75),
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
            pad_h = (bw - w) / 2
            print(f"[{ff[:4]} {fs:2.0f}px] len={len(line_txt):2d}, w={w:5.1f}px, box_w={bw:4d}px -> horiz padding = {pad_h:5.1f}px | '{line_txt}'")
            if pad_h < 16:
                print(f"  FAIL: pad_h {pad_h:.1f} < 16!")
                all_ok = False

    assert all_ok, "Some horizontal paddings failed!"
    print("\nALL HORIZONTAL PADDINGS >= 16px! (PASS)")

check_paddings("test_hosts_ini.svg")
