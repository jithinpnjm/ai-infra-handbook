import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180" width="1600" height="1180">
  <title>Check what Ansible built: five inventory commands in order</title>
  <desc>Visual infographic ladder of five inventory inspection commands in order: graph, vars, host, list yaml, and list-hosts with pattern matching.</desc>

  <!-- Background -->
  <rect width="1600" height="1180" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Check what Ansible built: five inventory commands in order</text>

  <!-- ==================== RUNG 1 ==================== -->
  <g id="rung-1">
    <rect x="40" y="95" width="1520" height="110" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <circle cx="95" cy="150" r="24" fill="#207448" />
    <!-- Tree Graph Icon (56px) -->
    <g transform="translate(138, 122)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="20" y="4" width="16" height="12" rx="2" />
      <rect x="4" y="38" width="16" height="12" rx="2" />
      <rect x="36" y="38" width="16" height="12" rx="2" />
      <line x1="28" y1="16" x2="28" y2="26" />
      <line x1="12" y1="26" x2="44" y2="26" />
      <line x1="12" y1="26" x2="12" y2="38" />
      <line x1="44" y1="26" x2="44" y2="38" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="95" y="160" text-anchor="middle" font-size="30" font-weight="bold" fill="#ffffff">1</tspan>
      <tspan x="214" y="138" text-anchor="start" font-family="monospace" font-size="30" font-weight="bold" fill="#207448"> ansible-inventory -i inventories/prod --graph: </tspan>
      <tspan font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">where did this host land? </tspan>
      <tspan x="214" y="174" text-anchor="start" font-family="sans-serif" font-size="24" fill="#303a36">tree of groups and hosts, no variable values, stays short</tspan>
    </text>
  </g>

  <!-- ==================== RUNG 2 ==================== -->
  <g id="rung-2">
    <rect x="40" y="245" width="1520" height="110" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <circle cx="95" cy="300" r="24" fill="#207448" />
    <!-- Tree with Vars Icon (56px) -->
    <g transform="translate(138, 272)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="6" width="18" height="14" rx="2" />
      <line x1="26" y1="13" x2="42" y2="13" />
      <circle cx="46" cy="13" r="3" fill="#207448" />
      <line x1="17" y1="20" x2="17" y2="32" />
      <line x1="17" y1="32" x2="28" y2="32" />
      <rect x="28" y="24" width="22" height="20" rx="3" />
      <line x1="33" y1="34" x2="45" y2="34" stroke-width="3" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="95" y="310" text-anchor="middle" font-size="30" font-weight="bold" fill="#ffffff">2</tspan>
      <tspan x="214" y="293" text-anchor="start" font-family="monospace" font-size="30" font-weight="bold" fill="#207448"> --graph --vars: </tspan>
      <tspan font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">the same tree with variables</tspan>
    </text>
  </g>

  <!-- ==================== RUNG 3 ==================== -->
  <g id="rung-3">
    <rect x="40" y="395" width="1520" height="110" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <circle cx="95" cy="450" r="24" fill="#207448" />
    <!-- Server Host with GPU Chip Icon (56px) -->
    <g transform="translate(138, 422)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="42" rx="4" />
      <circle cx="14" cy="16" r="2.5" fill="#207448" />
      <circle cx="22" cy="16" r="2.5" fill="#207448" />
      <rect x="18" y="24" width="20" height="16" rx="2" stroke-width="3" />
      <line x1="23" y1="21" x2="23" y2="24" stroke-width="2" />
      <line x1="33" y1="21" x2="33" y2="24" stroke-width="2" />
      <line x1="23" y1="40" x2="23" y2="43" stroke-width="2" />
      <line x1="33" y1="40" x2="33" y2="43" stroke-width="2" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="95" y="460" text-anchor="middle" font-size="30" font-weight="bold" fill="#ffffff">3</tspan>
      <tspan x="214" y="438" text-anchor="start" font-family="monospace" font-size="30" font-weight="bold" fill="#207448"> --host gpu001: </tspan>
      <tspan font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">what value does this host end up with? </tspan>
      <tspan x="214" y="474" text-anchor="start" font-family="sans-serif" font-size="24" fill="#303a36">fully merged variables for one host after every layer</tspan>
    </text>
  </g>

  <!-- ==================== RUNG 4 (ORANGE) ==================== -->
  <g id="rung-4">
    <rect x="40" y="545" width="1520" height="110" rx="14" fill="#e8f1ea" stroke="#db8129" stroke-width="3.5" />
    <circle cx="95" cy="600" r="24" fill="#207448" />
    <!-- Data Document / Diff Tool Icon (56px) -->
    <g transform="translate(138, 572)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 14 6 L 36 6 L 46 16 L 46 48 L 14 48 Z" />
      <polyline points="36,6 36,16 46,16" />
      <line x1="22" y1="26" x2="38" y2="26" stroke-width="3" />
      <line x1="22" y1="33" x2="38" y2="33" stroke-width="3" />
      <line x1="22" y1="40" x2="32" y2="40" stroke-width="3" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="95" y="610" text-anchor="middle" font-size="30" font-weight="bold" fill="#ffffff">4</tspan>
      <tspan x="214" y="588" text-anchor="start" font-family="monospace" font-size="30" font-weight="bold" fill="#207448"> --list --yaml: </tspan>
      <tspan font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">the whole inventory as data, </tspan>
      <tspan x="214" y="624" text-anchor="start" font-family="sans-serif" font-size="24" fill="#303a36">to save for a review because a diff tool can compare it</tspan>
    </text>
  </g>

  <!-- ==================== RUNG 5 ==================== -->
  <g id="rung-5">
    <rect x="40" y="695" width="1520" height="110" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <circle cx="95" cy="750" r="24" fill="#207448" />
    <!-- Pattern Match / Target Crosshair Icon (56px) -->
    <g transform="translate(138, 722)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="18" />
      <circle cx="28" cy="28" r="8" />
      <line x1="28" y1="4" x2="28" y2="10" />
      <line x1="28" y1="46" x2="28" y2="52" />
      <line x1="4" y1="28" x2="10" y2="28" />
      <line x1="46" y1="28" x2="52" y2="28" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="95" y="760" text-anchor="middle" font-size="30" font-weight="bold" fill="#ffffff">5</tspan>
      <tspan x="214" y="738" text-anchor="start" font-family="monospace" font-size="30" font-weight="bold" fill="#207448"> ansible gpu_h100 -i inventories/prod --list-hosts: </tspan>
      <tspan x="214" y="774" text-anchor="start" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">who would a pattern match</tspan>
    </text>
  </g>

  <!-- ==================== SIDE NOTE ==================== -->
  <g id="side-note">
    <rect x="40" y="845" width="1520" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" stroke-dasharray="8,6" />
    <!-- Alert / Caution Triangle Icon (56px) -->
    <g transform="translate(68, 884)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="28,4 52,48 4,48" />
      <line x1="28" y1="18" x2="28" y2="32" stroke-width="4" />
      <circle cx="28" cy="40" r="2.5" fill="#207448" stroke="none" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="148" y="898" font-size="26" font-weight="bold" fill="#207448">count the lines --list-hosts prints for the group: </tspan>
      <tspan font-family="sans-serif" font-size="24" fill="#303a36">a count smaller than </tspan>
      <tspan x="148" y="940" font-family="sans-serif" font-size="24" fill="#303a36">the number of machines you started is the first sign of the same-address collapse trap</tspan>
    </text>
  </g>

  <!-- ==================== TAKEAWAY BOTTOM BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="40" y="1020" width="1520" height="70" rx="12" fill="#207448" />
    <text x="800" y="1064" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Check the shape, then the final variables for one machine</text>
  </g>
</svg>'''

with open("test_v3.svg", "w") as f:
    f.write(svg_content)

tree = ET.parse("test_v3.svg")
root = tree.getroot()

expected_labels = [
    "Check what Ansible built: five inventory commands in order",
    "1 ansible-inventory -i inventories/prod --graph: where did this host land? tree of groups and hosts, no variable values, stays short",
    "2 --graph --vars: the same tree with variables",
    "3 --host gpu001: what value does this host end up with? fully merged variables for one host after every layer",
    "4 --list --yaml: the whole inventory as data, to save for a review because a diff tool can compare it",
    "5 ansible gpu_h100 -i inventories/prod --list-hosts: who would a pattern match",
    "count the lines --list-hosts prints for the group: a count smaller than the number of machines you started is the first sign of the same-address collapse trap",
    "Check the shape, then the final variables for one machine"
]

text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24! in '{full_text}'"
    text_elements.append((full_text, fs))

found_texts = [t for t, fs in text_elements]
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count {cnt} != 1"

extras = [t for t in found_texts if t not in expected_labels]
assert len(extras) == 0, f"Extras: {extras}"
print("All validations PASSED!")
