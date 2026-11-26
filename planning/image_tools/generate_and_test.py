import re
import xml.etree.ElementTree as ET
import subprocess
import pathlib

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>The Kubernetes Service path: seven checks in order</title>
  <desc>A vertical ladder of seven numbered rungs from top to bottom showing diagnostic checks for a failing Kubernetes Service.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="88" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">When a Service fails, confirm in order</text>

  <!-- Down the left side a thin arrow -->
  <line x1="50" y1="140" x2="50" y2="1064" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
  <text x="68" y="580" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="68" dy="0">read</tspan>
    <tspan x="68" dy="28">top to</tspan>
    <tspan x="68" dy="28">bottom</tspan>
  </text>

  <!-- ==================== RUNG 1: Pod ==================== -->
  <g id="rung-1">
    <rect x="175" y="140" width="975" height="92" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 1 -->
    <circle cx="215" cy="186" r="24" fill="#207448" />
    <text x="215" y="194" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
    <!-- Pod Outline Icon (56x56) -->
    <g transform="translate(250, 158)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="28,6 50,18 50,42 28,54 6,42 6,18" />
      <line x1="28" y1="6" x2="28" y2="30" />
      <line x1="6" y1="18" x2="28" y2="30" />
      <line x1="50" y1="18" x2="28" y2="30" />
      <line x1="28" y1="30" x2="28" y2="54" />
    </g>
    <!-- Text -->
    <text x="325" y="186" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Pod</text>
    <text x="325" y="216" font-family="monospace" font-size="24" fill="#303a36">call the pod IP and pod port directly from another pod</text>
  </g>

  <!-- ==================== RIGHT SIDE: Small Box Note ==================== -->
  <g id="small-box">
    <rect x="1190" y="140" width="370" height="92" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1215" y="180" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1215" dy="0">the first failing rung</tspan>
      <tspan x="1215" dy="30">is where to look</tspan>
    </text>
  </g>

  <!-- ==================== RUNG 2: Service ==================== -->
  <g id="rung-2">
    <rect x="175" y="274" width="1385" height="92" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 2 -->
    <circle cx="215" cy="320" r="24" fill="#207448" />
    <text x="215" y="328" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
    <!-- Service Gear Outline Icon (56x56) -->
    <g transform="translate(250, 292)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="12" />
      <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12 12 L 17 17 M 39 39 L 44 44 M 12 44 L 17 39 M 39 17 L 44 12" stroke-width="4" />
    </g>
    <!-- Text -->
    <text x="325" y="320" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Service</text>
    <text x="325" y="350" font-family="monospace" font-size="24" fill="#303a36">the Service exists, otherwise lookup fails with Name or service not known</text>
  </g>

  <!-- ==================== RUNG 3: DNS ==================== -->
  <g id="rung-3">
    <rect x="175" y="408" width="1385" height="92" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 3 -->
    <circle cx="215" cy="454" r="24" fill="#207448" />
    <text x="215" y="462" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
    <!-- DNS Globe Outline Icon (56x56) -->
    <g transform="translate(250, 426)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <ellipse cx="28" cy="28" rx="10" ry="22" />
      <line x1="6" y1="28" x2="50" y2="28" />
    </g>
    <!-- Text -->
    <text x="325" y="454" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">DNS</text>
    <text x="325" y="484" font-family="monospace" font-size="24" fill="#303a36">short, namespaced and full names resolve</text>
  </g>

  <!-- ==================== RUNG 4: Endpoints ==================== -->
  <g id="rung-4">
    <rect x="175" y="542" width="765" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 4 -->
    <circle cx="215" cy="602" r="24" fill="#207448" />
    <text x="215" y="610" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
    <!-- Endpoints Nodes Outline Icon (56x56) -->
    <g transform="translate(250, 574)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="16" r="6" />
      <circle cx="40" cy="16" r="6" />
      <circle cx="28" cy="42" r="6" />
      <line x1="16" y1="16" x2="28" y2="42" />
      <line x1="40" y1="16" x2="28" y2="42" />
      <line x1="16" y1="16" x2="40" y2="16" />
    </g>
    <!-- Text -->
    <text x="325" y="588" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Endpoints</text>
    <text x="325" y="618" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="325" dy="0">kubectl get endpointslices</tspan>
      <tspan x="325" dy="28">-l kubernetes.io/service-name=hostnames</tspan>
    </text>
  </g>

  <!-- ==================== ORANGE CALLOUT BESIDE RUNG 4 ==================== -->
  <!-- Single most important item highlighted in orange #db8129 -->
  <g id="orange-callout">
    <rect x="980" y="542" width="580" height="120" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3" />
    <text x="1010" y="582" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1010" dy="0" font-weight="bold" fill="#db8129">ENDPOINTS shows none means</tspan>
      <tspan x="1010" dy="28">the Service selector does not</tspan>
      <tspan x="1010" dy="28">match pod labels</tspan>
    </text>
  </g>

  <!-- ==================== RUNG 5: Ports ==================== -->
  <g id="rung-5">
    <rect x="175" y="704" width="1385" height="92" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 5 -->
    <circle cx="215" cy="750" r="24" fill="#207448" />
    <text x="215" y="758" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
    <!-- Ports Plug Outline Icon (56x56) -->
    <g transform="translate(250, 722)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="6" />
      <path d="M 18 10 L 18 24 L 24 24 L 24 38 L 32 38 L 32 24 L 38 24 L 38 10" />
    </g>
    <!-- Text -->
    <text x="325" y="750" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Ports</text>
    <text x="325" y="780" font-family="monospace" font-size="24" fill="#303a36">Service port listed, targetPort correct, named port matched</text>
  </g>

  <!-- ==================== RUNG 6: kube-proxy rules ==================== -->
  <g id="rung-6">
    <rect x="175" y="838" width="1385" height="92" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 6 -->
    <circle cx="215" cy="884" r="24" fill="#207448" />
    <text x="215" y="892" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">6</text>
    <!-- Shield / Rules Outline Icon (56x56) -->
    <g transform="translate(250, 856)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 L 48 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 L 8 14 Z" />
      <line x1="18" y1="26" x2="38" y2="26" />
      <line x1="28" y1="18" x2="28" y2="36" />
    </g>
    <!-- Text -->
    <text x="325" y="884" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">kube-proxy rules</text>
    <text x="325" y="914" font-family="monospace" font-size="24" fill="#303a36">iptables-save grep hostnames, or ipvsadm -ln</text>
  </g>

  <!-- ==================== RUNG 7: Conntrack ==================== -->
  <g id="rung-7">
    <rect x="175" y="972" width="1385" height="92" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Number circle 7 -->
    <circle cx="215" cy="1018" r="24" fill="#207448" />
    <text x="215" y="1026" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">7</text>
    <!-- Conntrack Table Outline Icon (56x56) -->
    <g transform="translate(250, 990)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="6" />
      <line x1="8" y1="20" x2="48" y2="20" />
      <line x1="8" y1="32" x2="48" y2="32" />
      <circle cx="15" cy="14" r="2" fill="#207448" />
      <circle cx="15" cy="26" r="2" fill="#207448" />
      <circle cx="15" cy="38" r="2" fill="#207448" />
    </g>
    <!-- Text -->
    <text x="325" y="1018" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Conntrack</text>
    <text x="325" y="1048" font-family="monospace" font-size="24" fill="#303a36">table usage, since iptables Service load balancing depends on connection tracking</text>
  </g>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <rect x="40" y="1100" width="1520" height="60" rx="12" fill="#207448" />
  <text x="800" y="1140" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack</text>
</svg>'''

with open("candidate_service_path.svg", "w") as f:
    f.write(svg_code)

print("Saved candidate_service_path.svg")

# Run full evaluation
root = ET.fromstring(svg_code)

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Canvas: viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600", f"Width {width} != 1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

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
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "When a Service fails, confirm in order",
    "read top to bottom",
    "Pod",
    "call the pod IP and pod port directly from another pod",
    "the first failing rung is where to look",
    "Service",
    "the Service exists, otherwise lookup fails with Name or service not known",
    "DNS",
    "short, namespaced and full names resolve",
    "Endpoints",
    "kubectl get endpointslices -l kubernetes.io/service-name=hostnames",
    "ENDPOINTS shows none means the Service selector does not match pod labels",
    "Ports",
    "Service port listed, targetPort correct, named port matched",
    "kube-proxy rules",
    "iptables-save grep hostnames, or ipvsadm -ln",
    "Conntrack",
    "table usage, since iptables Service load balancing depends on connection tracking",
    "Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack"
]

step_numbers = {"1", "2", "3", "4", "5", "6", "7"}
found_texts = [t for t, fs in text_elements]

print("\n4. Label check:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels) + len(step_numbers), f"Mismatch count: {len(found_texts)} vs {len(expected_labels) + len(step_numbers)}"
print("   [PASS] Exact label count matches: 19 expected labels + 7 step numbers!")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"

print("\n5. No forbidden words found in text (OK)")

# 6. Check orange count
orange_matches = re.findall(r'#db8129', svg_code, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 3, f"Unexpected orange count: {len(orange_matches)}"
print("   [PASS] Orange used only on the callout!")

# 7. Check arrows
markers = [e for e in root.iter() if "marker-end" in e.attrib]
print(f"\n7. Markers count: {len(markers)}")
assert len(markers) == 1, f"Expected 1 marker, found {len(markers)}"
print("   [PASS] Exactly 1 arrow down the left side!")

# 8. Check colors present
for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
    assert c in svg_code, f"Missing required palette color {c}!"
print("\n8. All palette colors present! (PASS)")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
