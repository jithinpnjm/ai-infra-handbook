import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1070" width="1600" height="1070">
  <title>Where policy engines hook a packet, and conntrack replies</title>
  <desc>Where policy engines hook a packet, and conntrack replies</desc>

  <defs>
    <!-- Green arrowhead (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1070" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Where policy engines hook a packet, and conntrack replies</text>

  <!-- ==================== TOP POD BOXES ==================== -->

  <!-- Left Pod Box: Pod egress is caught on the host-side veth -->
  <g id="box-pod-egress">
    <rect x="50" y="115" width="720" height="140" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Veth Icon (56px, green stroke 4) -->
    <g transform="translate(85, 157)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="10" width="22" height="36" rx="4" />
      <line x1="8" y1="20" x2="18" y2="20" />
      <line x1="8" y1="28" x2="18" y2="28" />
      <line x1="8" y1="36" x2="18" y2="36" />
      <rect x="32" y="10" width="22" height="36" rx="4" />
      <line x1="38" y1="20" x2="48" y2="20" />
      <line x1="38" y1="28" x2="48" y2="28" />
      <line x1="38" y1="36" x2="48" y2="36" />
      <path d="M 24 28 L 32 28" stroke-dasharray="2,2" />
    </g>
    <text x="430" y="172" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="430" dy="0">Pod egress is caught</tspan>
      <tspan x="430" dy="40">on the host-side veth</tspan>
    </text>
  </g>

  <!-- Right Pod Box: Pod ingress is caught when delivered to the veth -->
  <g id="box-pod-ingress">
    <rect x="830" y="115" width="720" height="140" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Veth Icon (56px, green stroke 4) -->
    <g transform="translate(865, 157)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="10" width="22" height="36" rx="4" />
      <line x1="8" y1="20" x2="18" y2="20" />
      <line x1="8" y1="28" x2="18" y2="28" />
      <line x1="8" y1="36" x2="18" y2="36" />
      <rect x="32" y="10" width="22" height="36" rx="4" />
      <line x1="38" y1="20" x2="48" y2="20" />
      <line x1="38" y1="28" x2="48" y2="28" />
      <line x1="38" y1="36" x2="48" y2="36" />
      <path d="M 24 28 L 32 28" />
    </g>
    <text x="1210" y="172" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="1210" dy="0">Pod ingress is caught</tspan>
      <tspan x="1210" dy="40">when delivered to the veth</tspan>
    </text>
  </g>

  <!-- ==================== MIDDLE ROW: NETFILTER HOOKS ==================== -->

  <!-- Container for the horizontal netfilter path -->
  <rect x="50" y="305" width="1500" height="220" rx="18" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Note: iptables and nftables use these hooks -->
  <text x="800" y="348" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">iptables and nftables use these hooks</text>

  <!-- Connecting pipeline track behind hook boxes -->
  <line x1="210" y1="435" x2="1390" y2="435" stroke="#207448" stroke-width="6" stroke-linecap="round" />

  <!-- Hook 1: PREROUTING -->
  <g id="hook-prerouting">
    <rect x="85" y="375" width="250" height="120" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Routing Icon (green stroke 4) -->
    <g transform="translate(187, 390)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="23" cy="18" r="14" />
      <path d="M 15 18 L 23 26 L 31 18" />
    </g>
    <text x="210" y="470" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">PREROUTING</text>
  </g>

  <!-- Hook 2: FORWARD -->
  <g id="hook-forward">
    <rect x="380" y="375" width="250" height="120" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Forward Icon (green stroke 4) -->
    <g transform="translate(482, 390)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="23" cy="18" r="14" />
      <path d="M 13 18 L 33 18" />
      <path d="M 25 10 L 33 18 L 25 26" />
    </g>
    <text x="505" y="470" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">FORWARD</text>
  </g>

  <!-- Hook 3: INPUT -->
  <g id="hook-input">
    <rect x="675" y="375" width="250" height="120" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Inbound Icon (green stroke 4) -->
    <g transform="translate(777, 390)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="9" y="4" width="28" height="28" rx="4" />
      <path d="M 4 18 L 23 18" />
      <path d="M 17 12 L 23 18 L 17 24" />
    </g>
    <text x="800" y="470" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">INPUT</text>
  </g>

  <!-- Hook 4: OUTPUT -->
  <g id="hook-output">
    <rect x="970" y="375" width="250" height="120" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Outbound Icon (green stroke 4) -->
    <g transform="translate(1072, 390)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="9" y="4" width="28" height="28" rx="4" />
      <path d="M 23 18 L 42 18" />
      <path d="M 36 12 L 42 18 L 36 24" />
    </g>
    <text x="1095" y="470" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">OUTPUT</text>
  </g>

  <!-- Hook 5: POSTROUTING -->
  <g id="hook-postrouting">
    <rect x="1265" y="375" width="250" height="120" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Postrouting Icon (green stroke 4) -->
    <g transform="translate(1367, 390)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="23" cy="18" r="14" />
      <path d="M 15 18 L 23 10 L 31 18" />
    </g>
    <text x="1390" y="470" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">POSTROUTING</text>
  </g>

  <!-- ==================== ARROW: CONNTRACK -> FORWARD ==================== -->

  <!-- Single arrow from conntrack table back to FORWARD box -->
  <line x1="505" y1="675" x2="505" y2="495" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- Label card beside the arrow -->
  <g id="label-established">
    <rect x="85" y="538" width="390" height="94" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="280" y="575" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="280" dy="0">ESTABLISHED,RELATED</tspan>
      <tspan x="280" dy="32">matches, replies pass</tspan>
    </text>
  </g>

  <!-- ==================== CONNTRACK TABLE BOX ==================== -->

  <!-- Conntrack table box with ORANGE outline as the stateful check -->
  <g id="box-conntrack-table">
    <rect x="180" y="675" width="1240" height="235" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="4" />

    <!-- Stateful Shield Icon (green stroke 4) -->
    <g transform="translate(202, 767)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 24 4 L 48 12 L 48 28 C 48 42 34 52 24 56 C 14 52 0 42 0 28 L 0 12 Z" />
      <circle cx="24" cy="28" r="6" fill="#207448" />
    </g>

    <!-- Row 1: Connection entry (pair of addresses and ports) -->
    <g id="entry-row-1" transform="translate(270, 695)">
      <rect x="0" y="0" width="1120" height="58" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <!-- Left address slot -->
      <rect x="15" y="10" width="460" height="38" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
      <circle cx="35" cy="29" r="6" fill="#207448" />
      <rect x="55" y="21" width="260" height="16" rx="4" fill="#207448" opacity="0.8" />
      <rect x="330" y="21" width="125" height="16" rx="4" fill="#207448" opacity="0.5" />
      <!-- Middle bidirectional link symbol -->
      <g transform="translate(525, 17)" stroke="#207448" stroke-width="3" fill="none">
        <path d="M 0 12 L 70 12" />
        <path d="M 10 4 L 0 12 L 10 20" />
        <path d="M 60 4 L 70 12 L 60 20" />
      </g>
      <!-- Right address slot -->
      <rect x="645" y="10" width="460" height="38" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
      <circle cx="665" cy="29" r="6" fill="#207448" />
      <rect x="685" y="21" width="260" height="16" rx="4" fill="#207448" opacity="0.8" />
      <rect x="960" y="21" width="125" height="16" rx="4" fill="#207448" opacity="0.5" />
    </g>

    <!-- Row 2: Connection entry (pair of addresses and ports) -->
    <g id="entry-row-2" transform="translate(270, 765)">
      <rect x="0" y="0" width="1120" height="58" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <!-- Left address slot -->
      <rect x="15" y="10" width="460" height="38" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
      <circle cx="35" cy="29" r="6" fill="#207448" />
      <rect x="55" y="21" width="280" height="16" rx="4" fill="#207448" opacity="0.8" />
      <rect x="350" y="21" width="105" height="16" rx="4" fill="#207448" opacity="0.5" />
      <!-- Middle bidirectional link symbol -->
      <g transform="translate(525, 17)" stroke="#207448" stroke-width="3" fill="none">
        <path d="M 0 12 L 70 12" />
        <path d="M 10 4 L 0 12 L 10 20" />
        <path d="M 60 4 L 70 12 L 60 20" />
      </g>
      <!-- Right address slot -->
      <rect x="645" y="10" width="460" height="38" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
      <circle cx="665" cy="29" r="6" fill="#207448" />
      <rect x="685" y="21" width="280" height="16" rx="4" fill="#207448" opacity="0.8" />
      <rect x="980" y="21" width="105" height="16" rx="4" fill="#207448" opacity="0.5" />
    </g>

    <!-- Row 3: Connection entry (pair of addresses and ports) -->
    <g id="entry-row-3" transform="translate(270, 835)">
      <rect x="0" y="0" width="1120" height="58" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <!-- Left address slot -->
      <rect x="15" y="10" width="460" height="38" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
      <circle cx="35" cy="29" r="6" fill="#207448" />
      <rect x="55" y="21" width="240" height="16" rx="4" fill="#207448" opacity="0.8" />
      <rect x="310" y="21" width="145" height="16" rx="4" fill="#207448" opacity="0.5" />
      <!-- Middle bidirectional link symbol -->
      <g transform="translate(525, 17)" stroke="#207448" stroke-width="3" fill="none">
        <path d="M 0 12 L 70 12" />
        <path d="M 10 4 L 0 12 L 10 20" />
        <path d="M 60 4 L 70 12 L 60 20" />
      </g>
      <!-- Right address slot -->
      <rect x="645" y="10" width="460" height="38" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
      <circle cx="665" cy="29" r="6" fill="#207448" />
      <rect x="685" y="21" width="240" height="16" rx="4" fill="#207448" opacity="0.8" />
      <rect x="940" y="21" width="145" height="16" rx="4" fill="#207448" opacity="0.5" />
    </g>
  </g>

  <!-- ==================== BOTTOM NOTE ==================== -->
  <rect x="80" y="955" width="1440" height="70" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <text x="800" y="998" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">A reply is matched against the open-connection list first, so the policy is not read again.</text>
</svg>'''

root = ET.fromstring(svg_code)

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check text elements and font-size >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for t, fs in text_elements:
    print(f"   [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Where policy engines hook a packet, and conntrack replies",
    "Pod egress is caught on the host-side veth",
    "Pod ingress is caught when delivered to the veth",
    "iptables and nftables use these hooks",
    "PREROUTING",
    "FORWARD",
    "INPUT",
    "OUTPUT",
    "POSTROUTING",
    "ESTABLISHED,RELATED matches, replies pass",
    "A reply is matched against the open-connection list first, so the policy is not read again."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
orange_matches = re.findall(r'#db8129', svg_code, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Expected exactly 1 orange usage, got {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 1, f"Expected 1 arrow, got {total_arrows}"

pathlib.Path("perfect_candidate.svg").write_text(svg_code)
print("\nSaved perfect_candidate.svg!")
