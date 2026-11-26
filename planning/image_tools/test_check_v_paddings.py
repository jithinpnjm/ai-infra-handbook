import xml.etree.ElementTree as ET

tree = ET.parse("test_hosts_ini.svg")
root = tree.getroot()

boxes = {
    "[gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12": (116, 124),
    "a group collects hosts that share a role": (250, 56),
    "each host has a name and optionally an address": (316, 90),
    "[login] login01 ansible_host=10.0.10.5": (416, 90),
    "[cluster:children] gpu login": (516, 90),
    "[cluster:vars] ansible_user=automation, ansible_python_interpreter=/usr/bin/python3": (616, 124),
    "cluster": (130, 70),
    "ansible_user and interpreter apply to all three machines": (240, 90),
    "gpu": (420, 190),
    "login": (420, 190),
    "a group of groups, written with :children, lets one command reach every member: a play aimed at cluster reaches all three machines": (780, 90),
    "ansible-inventory --graph (run first: shows the nesting at a glance), --list, --host gpu01": (890, 75),
    "a node missing from the inventory quietly misses every change you make": (985, 75),
    "The inventory is the phone book of your fleet": (1080, 75),
}

all_ok = True
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = " ".join("".join(elem.itertext()).split())
    if full_text == "Reading hosts.ini: hosts, groups, groups of groups":
        continue
    fs = float(elem.attrib['font-size'])
    by, bh = boxes[full_text]
    
    y = float(elem.attrib.get('y', 0))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if not tspans:
        top_y = y - fs * 0.75
        bot_y = y + fs * 0.25
    else:
        # compute lines
        curr_y = y
        line_ys = []
        for tsp in tspans:
            dy = float(tsp.attrib.get('dy', 0))
            curr_y += dy
            line_ys.append(curr_y)
        top_y = line_ys[0] - fs * 0.75
        bot_y = line_ys[-1] + fs * 0.25
        
    pad_top = top_y - by
    pad_bot = (by + bh) - bot_y
    print(f"[{fs:2.0f}px] Box y={by}..{by+bh} (h={bh}): text top={top_y:.1f}, bot={bot_y:.1f} -> pad_top={pad_top:.1f}px, pad_bot={pad_bot:.1f}px | '{full_text[:35]}...'")
    if pad_top < 16:
        print(f"  FAIL: pad_top {pad_top:.1f} < 16!")
        all_ok = False
    if pad_bot < 16:
        print(f"  FAIL: pad_bot {pad_bot:.1f} < 16!")
        all_ok = False

assert all_ok, "Some vertical paddings failed!"
print("\nALL VERTICAL PADDINGS >= 16px! (PASS)")
