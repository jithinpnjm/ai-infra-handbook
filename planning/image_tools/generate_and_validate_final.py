import xml.etree.ElementTree as ET
import re
import pathlib

def generate_svg():
    W = 1600
    H = 1200
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>Reading hosts.ini: hosts, groups, groups of groups</title>')
    svg.append('  <desc>Visual infographic explaining hosts.ini structure, inventory nesting, group of groups with children, vars inheritance, and inspection commands.</desc>')
    svg.append('  <defs>')
    
    # Arrow marker green
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')

    # Arrow marker orange
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg.append('    </marker>')

    # 56px Outline Icons (stroke-width 4, green #207448)
    # 1. Icon: Document / INI File
    svg.append('    <g id="icon-file" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 10 4 L 34 4 L 46 16 L 46 52 L 10 52 Z" />')
    svg.append('      <polyline points="34,4 34,16 46,16" />')
    svg.append('      <line x1="18" y1="24" x2="38" y2="24" />')
    svg.append('      <line x1="18" y1="32" x2="38" y2="32" />')
    svg.append('      <line x1="18" y1="40" x2="30" y2="40" />')
    svg.append('    </g>')

    # 2. Icon: Hierarchical Tree / Group of Groups
    svg.append('    <g id="icon-tree" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="20" y="6" width="16" height="12" rx="3" fill="#ffffff" />')
    svg.append('      <rect x="6" y="38" width="16" height="12" rx="3" fill="#ffffff" />')
    svg.append('      <rect x="34" y="38" width="16" height="12" rx="3" fill="#ffffff" />')
    svg.append('      <path d="M 28 18 L 28 28 L 14 28 L 14 38 M 28 28 L 42 28 L 42 38" />')
    svg.append('    </g>')

    # 3. Icon: Server / GPU Host (Compute chip + chassis)
    svg.append('    <g id="icon-server" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="44" height="18" rx="4" fill="#ffffff" />')
    svg.append('      <rect x="6" y="30" width="44" height="18" rx="4" fill="#ffffff" />')
    svg.append('      <circle cx="14" cy="17" r="2.5" fill="#207448" />')
    svg.append('      <circle cx="22" cy="17" r="2.5" fill="#207448" />')
    svg.append('      <line x1="32" y1="17" x2="42" y2="17" />')
    svg.append('      <circle cx="14" cy="39" r="2.5" fill="#207448" />')
    svg.append('      <circle cx="22" cy="39" r="2.5" fill="#207448" />')
    svg.append('      <line x1="32" y1="39" x2="42" y2="39" />')
    svg.append('    </g>')

    # 4. Icon: Terminal Window
    svg.append('    <g id="icon-terminal" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="8" width="48" height="40" rx="6" fill="#ffffff" />')
    svg.append('      <line x1="4" y1="20" x2="52" y2="20" />')
    svg.append('      <circle cx="11" cy="14" r="2" fill="#207448" />')
    svg.append('      <circle cx="17" cy="14" r="2" fill="#207448" />')
    svg.append('      <path d="M 12 30 L 18 35 L 12 40" />')
    svg.append('      <line x1="22" y1="40" x2="34" y2="40" />')
    svg.append('    </g>')

    # 5. Icon: Alert Triangle
    svg.append('    <g id="icon-alert" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 50 46 L 6 46 Z" fill="#ffffff" />')
    svg.append('      <line x1="28" y1="20" x2="28" y2="32" />')
    svg.append('      <circle cx="28" cy="39" r="2" fill="#207448" />')
    svg.append('    </g>')

    # 6. Icon: Directory / Phone Book
    svg.append('    <g id="icon-book" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 8 10 C 16 6 28 6 28 14 L 28 48 C 28 40 16 40 8 44 Z" />')
    svg.append('      <path d="M 48 10 C 40 6 28 6 28 14 L 28 48 C 28 40 40 40 48 44 Z" />')
    svg.append('    </g>')

    svg.append('  </defs>')

    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')

    # Title (48px bold)
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Reading hosts.ini: hosts, groups, groups of groups</text>')

    # ================= LEFT CONTAINER: ANNOTATED INI FILE =================
    svg.append('  <g id="panel-ini">')
    svg.append('    <rect x="40" y="100" width="740" height="655" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-file" x="708" y="112" />')
    
    # 1. Section: [gpu]
    svg.append('    <rect x="60" y="116" width="630" height="124" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="375" y="154" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="375" dy="0">[gpu]</tspan>')
    svg.append('      <tspan x="375" dy="32">gpu01 ansible_host=10.0.10.11,</tspan>')
    svg.append('      <tspan x="375" dy="32">gpu02 ansible_host=10.0.10.12</tspan>')
    svg.append('    </text>')

    # 2. Callout 2: a group collects hosts that share a role
    svg.append('    <rect x="60" y="248" width="700" height="60" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="410" y="284" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">a group collects hosts that share a role</text>')

    # 3. Callout 1: each host has a name and optionally an address
    svg.append('    <rect x="60" y="316" width="700" height="92" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="410" y="352" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="410" dy="0">each host has a name and</tspan>')
    svg.append('      <tspan x="410" dy="32">optionally an address</tspan>')
    svg.append('    </text>')

    # 4. Section: [login]
    svg.append('    <rect x="60" y="416" width="700" height="92" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="410" y="452" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="410" dy="0">[login]</tspan>')
    svg.append('      <tspan x="410" dy="32">login01 ansible_host=10.0.10.5</tspan>')
    svg.append('    </text>')

    # 5. Section: [cluster:children]
    svg.append('    <rect x="60" y="516" width="700" height="92" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="410" y="552" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="410" dy="0">[cluster:children]</tspan>')
    svg.append('      <tspan x="410" dy="32">gpu login</tspan>')
    svg.append('    </text>')

    # 6. Section: [cluster:vars]
    svg.append('    <rect x="60" y="616" width="700" height="124" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="410" y="654" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="410" dy="0">[cluster:vars]</tspan>')
    svg.append('      <tspan x="410" dy="32">ansible_user=automation,</tspan>')
    svg.append('      <tspan x="410" dy="32">ansible_python_interpreter=/usr/bin/python3</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ================= RIGHT CONTAINER: TREE =================
    svg.append('  <g id="panel-tree">')
    svg.append('    <rect x="820" y="100" width="740" height="655" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-tree" x="1488" y="112" />')

    # Tree root: cluster
    svg.append('    <rect x="1050" y="130" width="280" height="70" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1190" y="175" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">cluster</text>')

    # Vars box attached to cluster
    svg.append('    <line x1="1190" y1="200" x2="1190" y2="240" stroke="#207448" stroke-width="2.5" stroke-dasharray="6,4" />')
    svg.append('    <rect x="910" y="240" width="560" height="92" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1190" y="276" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1190" dy="0">ansible_user and interpreter</tspan>')
    svg.append('      <tspan x="1190" dy="32">apply to all three machines</tspan>')
    svg.append('    </text>')

    # Branch connections from cluster down to gpu and login
    svg.append('    <path d="M 1190 332 L 1190 375 L 990 375 L 990 416" fill="none" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
    svg.append('    <path d="M 1190 375 L 1390 375 L 1390 416" fill="none" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # Child 1: gpu
    svg.append('    <rect x="860" y="420" width="260" height="190" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="990" y="468" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">gpu</text>')
    svg.append('    <use href="#icon-server" x="900" y="500" />')
    svg.append('    <use href="#icon-server" x="1024" y="500" />')

    # Child 2: login
    svg.append('    <rect x="1260" y="420" width="260" height="190" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1390" y="468" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">login</text>')
    svg.append('    <use href="#icon-server" x="1362" y="500" />')
    svg.append('  </g>')

    # ================= CALLOUT 3: GROUP OF GROUPS (ORANGE) =================
    svg.append('  <g id="callout-orange">')
    svg.append('    <rect x="40" y="775" width="1520" height="100" rx="14" fill="#fff9f5" stroke="#db8129" stroke-width="3" />')
    svg.append('    <text x="800" y="818" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="800" dy="0">a group of groups, written with :children, lets one command reach every</tspan>')
    svg.append('      <tspan x="800" dy="34">member: a play aimed at cluster reaches all three machines</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ================= COMMANDS STRIP =================
    svg.append('  <g id="strip-commands">')
    svg.append('    <rect x="40" y="890" width="1520" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <use href="#icon-terminal" x="64" y="902" />')
    svg.append('    <text x="800" y="940" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">ansible-inventory --graph (run first: shows the nesting at a glance), --list, --host gpu01</text>')
    svg.append('  </g>')

    # ================= WARNING STRIP =================
    svg.append('  <g id="strip-warning">')
    svg.append('    <rect x="40" y="985" width="1520" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <use href="#icon-alert" x="64" y="997" />')
    svg.append('    <text x="800" y="1035" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">a node missing from the inventory quietly misses every change you make</text>')
    svg.append('  </g>')

    # ================= BOTTOM BAR =================
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1080" width="1520" height="80" rx="14" fill="#207448" />')
    svg.append('    <use href="#icon-book" x="64" y="1092" />')
    svg.append('    <text x="800" y="1129" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">The inventory is the phone book of your fleet</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

svg_str = generate_svg()
pathlib.Path("final_hosts_ini.svg").write_text(svg_str, encoding="utf-8")
print("Wrote final_hosts_ini.svg successfully.")

# Run comprehensive validation
tree = ET.parse("final_hosts_ini.svg")
root = tree.getroot()

# 1. Structure
children = list(root)
assert children[0].tag.split('}')[-1] == 'title'
assert children[1].tag.split('}')[-1] == 'desc'

# 2. Dimensions
assert root.get('width') == "1600"
assert root.get('height') == "1200"
assert root.get('viewBox') == "0 0 1600 1200"

# 3. Expected labels
expected_labels = [
    "Reading hosts.ini: hosts, groups, groups of groups",
    "[gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12",
    "a group collects hosts that share a role",
    "each host has a name and optionally an address",
    "[login] login01 ansible_host=10.0.10.5",
    "[cluster:children] gpu login",
    "[cluster:vars] ansible_user=automation, ansible_python_interpreter=/usr/bin/python3",
    "cluster",
    "ansible_user and interpreter apply to all three machines",
    "gpu",
    "login",
    "a group of groups, written with :children, lets one command reach every member: a play aimed at cluster reaches all three machines",
    "ansible-inventory --graph (run first: shows the nesting at a glance), --list, --host gpu01",
    "a node missing from the inventory quietly misses every change you make",
    "The inventory is the phone book of your fleet"
]

found_texts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    t = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    found_texts.append(t)
    fs = float(elem.attrib['font-size'])
    assert fs >= 24, f"Font size {fs} < 24 for '{t}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        if 'font-size' in tsp.attrib:
            assert float(tsp.attrib['font-size']) >= 24

for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Label '{exp}' count {cnt} != 1"

assert len(found_texts) == len(expected_labels), f"Text count mismatch {len(found_texts)} != {len(expected_labels)}"

# 4. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for w in words:
        assert w not in forbidden, f"Forbidden word '{w}' in '{t}'"

# 5. Orange check
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
assert 1 <= len(orange_matches) <= 4, f"Orange count {len(orange_matches)}"

# 6. Padding check
boxes = {
    "[gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12": (60, 116, 630, 124),
    "a group collects hosts that share a role": (60, 248, 700, 60),
    "each host has a name and optionally an address": (60, 316, 700, 92),
    "[login] login01 ansible_host=10.0.10.5": (60, 416, 700, 92),
    "[cluster:children] gpu login": (60, 516, 700, 92),
    "[cluster:vars] ansible_user=automation, ansible_python_interpreter=/usr/bin/python3": (60, 616, 700, 124),
    "cluster": (1050, 130, 280, 70),
    "ansible_user and interpreter apply to all three machines": (910, 240, 560, 92),
    "gpu": (860, 420, 260, 190),
    "login": (1260, 420, 260, 190),
    "a group of groups, written with :children, lets one command reach every member: a play aimed at cluster reaches all three machines": (40, 775, 1520, 100),
    "ansible-inventory --graph (run first: shows the nesting at a glance), --list, --host gpu01": (40, 890, 1520, 80),
    "a node missing from the inventory quietly misses every change you make": (40, 985, 1520, 80),
    "The inventory is the phone book of your fleet": (40, 1080, 1520, 80),
}

for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = " ".join("".join(elem.itertext()).split())
    if full_text == "Reading hosts.ini: hosts, groups, groups of groups":
        continue
    fs = float(elem.attrib['font-size'])
    bx, by, bw, bh = boxes[full_text]
    
    y = float(elem.attrib.get('y', 0))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if not tspans:
        lines = [(full_text, elem.attrib.get('font-family', 'sans-serif'))]
        top_y = y - fs * 0.75
        bot_y = y + fs * 0.25
    else:
        lines = []
        curr_y = y
        line_ys = []
        for tsp in tspans:
            dy = float(tsp.attrib.get('dy', 0))
            curr_y += dy
            line_ys.append(curr_y)
            txt = tsp.text.strip()
            ff = tsp.attrib.get('font-family', elem.attrib.get('font-family', 'sans-serif'))
            lines.append((txt, ff))
        top_y = line_ys[0] - fs * 0.75
        bot_y = line_ys[-1] + fs * 0.25
        
    pad_top = top_y - by
    pad_bot = (by + bh) - bot_y
    assert pad_top >= 16, f"pad_top {pad_top:.1f} < 16 for '{full_text}'"
    assert pad_bot >= 16, f"pad_bot {pad_bot:.1f} < 16 for '{full_text}'"
    
    for line_txt, ff in lines:
        is_mono = 'mono' in ff
        mult = 0.62 if is_mono else 0.60
        w = len(line_txt) * fs * mult
        pad_h = (bw - w) / 2
        assert pad_h >= 16, f"pad_h {pad_h:.1f} < 16 for '{line_txt}'"

print("ALL VERIFICATIONS AND ASSERTIONS PASSED 100%!")
