import xml.etree.ElementTree as ET
import re, pathlib, subprocess

svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1120" width="1600" height="1120">
  <title>Environment variables versus DNS for finding a Service</title>
  <desc>Visual comparison between discovering Kubernetes Services via environment variables versus CoreDNS, illustrating launch-time injection limits and real-time DNS resolution.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1120" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="62" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Environment variables versus DNS for finding a Service</text>

  <!-- ==================== TIMELINE 1: ENVIRONMENT VARIABLES ==================== -->
  <g id="timeline-1">
    <!-- Panel Container -->
    <rect x="40" y="95" width="1520" height="505" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

    <!-- Icon: Sliders / config (56px) -->
    <g transform="translate(65, 115)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round">
      <line x1="8" y1="14" x2="48" y2="14" />
      <circle cx="22" cy="14" r="5" fill="#e8f1ea" />
      <line x1="8" y1="28" x2="48" y2="28" />
      <circle cx="36" cy="28" r="5" fill="#e8f1ea" />
      <line x1="8" y1="42" x2="48" y2="42" />
      <circle cx="18" cy="42" r="5" fill="#e8f1ea" />
    </g>

    <!-- Heading (32px bold) -->
    <text x="135" y="152" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Environment variables</text>

    <!-- Row 1: Node 1 -> Arrow -> Node 2 -->
    <!-- Node 1: Service created at T1 -->
    <rect x="65" y="185" width="370" height="130" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(80, 222)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 38,28" />
    </g>
    <text x="285" y="258" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">Service created at T1</text>

    <!-- Arrow: then (1 arrow with marker-end) -->
    <line x1="435" y1="250" x2="495" y2="250" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

    <!-- Node 2: pod created at T2 receives... -->
    <rect x="495" y="185" width="1040" height="130" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(515, 222)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="4" />
      <line x1="6" y1="20" x2="50" y2="20" />
      <circle cx="14" cy="14" r="2" fill="#207448" />
      <circle cx="22" cy="14" r="2" fill="#207448" />
    </g>
    <text x="590" y="228" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="590" dy="0">pod created at T2 receives <tspan font-family="monospace">NGINX_SERVICE_HOST=10.110.34.183</tspan> and <tspan font-family="monospace">NGINX_SERVICE_PORT=80</tspan> </tspan><tspan x="590" dy="38">only for Services that existed before the pod</tspan></text>

    <!-- Row 2: second pod & badge -->
    <!-- Second pod box -->
    <rect x="65" y="335" width="970" height="95" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(80, 354)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="20" stroke-dasharray="24 10" />
      <polyline points="38,14 44,22 36,28" />
    </g>
    <text x="560" y="390" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">a second pod created before the Service has no variables until it restarts</text>

    <!-- Red badge: printed at birth, never updated -->
    <rect x="1055" y="335" width="480" height="95" rx="14" fill="#fee2e2" stroke="#dc2626" stroke-width="2.5" />
    <g transform="translate(1070, 354)" stroke="#dc2626" stroke-width="4" fill="none" stroke-linecap="round">
      <circle cx="28" cy="28" r="20" />
      <line x1="28" y1="16" x2="28" y2="28" />
      <circle cx="28" cy="36" r="2" fill="#dc2626" />
    </g>
    <text x="1305" y="390" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#dc2626">badge printed at birth, never updated</text>

    <!-- Row 3: Large namespace note (Orange highlight container) -->
    <rect x="65" y="450" width="1470" height="130" rx="12" fill="#fffaf5" stroke="#db8129" stroke-width="3" />
    <g transform="translate(85, 487)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 50 46 L 6 46 Z" />
      <line x1="28" y1="20" x2="28" y2="32" />
      <circle cx="28" cy="40" r="2" fill="#207448" />
    </g>
    <text x="160" y="490" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="160" dy="0">in a namespace with 2,000 Services kubelet injects 10,000+ variables, which can exceed the </tspan><tspan x="160" dy="34">Linux execve environment size limit (<tspan font-family="monospace">MAX_ARG_STRLEN</tspan>) and fail container start; set <tspan font-family="monospace">enableServiceLinks false</tspan></tspan></text>
  </g>

  <!-- ==================== TIMELINE 2: DNS (CoreDNS) ==================== -->
  <g id="timeline-2">
    <!-- Panel Container -->
    <rect x="40" y="620" width="1520" height="360" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

    <!-- Icon: Globe / DNS (56px) -->
    <g transform="translate(65, 638)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round">
      <circle cx="28" cy="28" r="22" />
      <ellipse cx="28" cy="28" rx="10" ry="22" />
      <line x1="6" y1="28" x2="50" y2="28" />
    </g>

    <!-- Heading (32px bold) -->
    <text x="135" y="675" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">DNS (CoreDNS)</text>

    <!-- Item 1: name resolves... -->
    <rect x="65" y="710" width="1470" height="110" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(85, 737)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="10" width="34" height="40" rx="3" />
      <line x1="16" y1="20" x2="32" y2="20" />
      <line x1="16" y1="28" x2="32" y2="28" />
      <circle cx="38" cy="38" r="8" />
      <line x1="44" y1="44" x2="50" y2="50" />
    </g>
    <text x="160" y="773" font-family="sans-serif" font-size="24" fill="#303a36">name <tspan font-family="monospace">my-svc.my-ns.svc.cluster.local</tspan> resolves as soon as the Service exists; phone book anyone can look up any time</text>

    <!-- Item 2: records... -->
    <rect x="65" y="840" width="1470" height="110" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(85, 867)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="4" />
      <polyline points="14,20 20,26 30,16" />
      <line x1="36" y1="22" x2="44" y2="22" />
      <polyline points="14,34 20,40 30,30" />
      <line x1="36" y1="36" x2="44" y2="36" />
    </g>
    <text x="160" y="903" font-family="sans-serif" font-size="24" fill="#303a36">A and AAAA for the ClusterIP, SRV for named ports; headless returns pod IPs</text>
  </g>

  <!-- ==================== FOOTER ==================== -->
  <g id="footer">
    <rect x="40" y="1000" width="1520" height="90" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(65, 1017)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="20" />
      <line x1="28" y1="18" x2="28" y2="28" />
      <circle cx="28" cy="38" r="2" fill="#207448" />
    </g>
    <text x="800" y="1038" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="800" dy="0">Kubernetes annotation values must be quoted strings, </tspan><tspan x="800" dy="32">the text true in quotes, not a bare YAML boolean</tspan></text>
  </g>
</svg>"""

pathlib.Path("final_test.svg").write_text(svg)

# Full validation script
root = ET.fromstring(svg)

# 1. First children
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
assert first_tag == "title", f"First tag {first_tag}"
assert second_tag == "desc", f"Second tag {second_tag}"
print("1. Structure: PASS (<title> and <desc> are first children)")

# 2. Dimensions
width = root.get("width")
height = root.get("height")
viewBox = root.get("viewBox")
assert width == "1600"
assert height == "1120"
assert viewBox == "0 0 1600 1120"
print("2. Canvas: PASS (1600x1120)")

# 3. Text font-size >= 24
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

print(f"3. Font sizes: PASS ({len(text_elements)} text elements all >= 24px)")

# 4. Expected labels
expected_labels = [
    "Environment variables versus DNS for finding a Service",
    "Environment variables",
    "Service created at T1",
    "pod created at T2 receives NGINX_SERVICE_HOST=10.110.34.183 and NGINX_SERVICE_PORT=80 only for Services that existed before the pod",
    "a second pod created before the Service has no variables until it restarts",
    "badge printed at birth, never updated",
    "in a namespace with 2,000 Services kubelet injects 10,000+ variables, which can exceed the Linux execve environment size limit (MAX_ARG_STRLEN) and fail container start; set enableServiceLinks false",
    "DNS (CoreDNS)",
    "name my-svc.my-ns.svc.cluster.local resolves as soon as the Service exists; phone book anyone can look up any time",
    "A and AAAA for the ClusterIP, SRV for named ports; headless returns pod IPs",
    "Kubernetes annotation values must be quoted strings, the text true in quotes, not a bare YAML boolean"
]

found_texts = [t for t, fs in text_elements]
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count {cnt} != 1"
    print(f"   [FOUND] '{exp[:50]}...'")

extras = [t for t in found_texts if t not in expected_labels]
assert len(extras) == 0, f"Unexpected extras: {extras}"
print("4. Content fidelity: PASS (All labels present once, zero extra text)")

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("5. Forbidden words: PASS (None found)")

# 6. Orange occurrences
orange_matches = re.findall(r'#db8129', svg, re.IGNORECASE)
print(f"6. Orange occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Expected exactly 1 orange match, got {len(orange_matches)}"
print("   PASS: Exactly 1 orange (#db8129) occurrence")

# 7. Arrow count
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"7. Arrow count: {total_arrows}")
assert total_arrows == 1, f"Expected exactly 1 arrow, got {total_arrows}"
print("   PASS: Exactly 1 arrow")

print("\nALL 7 STRICT AUDIT CHECKS PASSED PERFECTLY!")
