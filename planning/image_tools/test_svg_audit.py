import xml.etree.ElementTree as ET
import re

svg_candidate = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 960" width="1600" height="960">
  <title>Two tools that say which rank is stuck</title>
  <desc>Visual infographic comparing PyTorch flight recorder and NCCL RAS for diagnosing hung distributed training jobs, and showing the combined diagnostic flow.</desc>

  <!-- Background -->
  <rect width="1600" height="960" fill="#f5f8f5"/>

  <!-- Title: 48px bold -->
  <text x="800" y="70" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Two tools that say which rank is stuck</text>

  <!-- ==================== TOOL CARDS ==================== -->
  <!-- Card 1: PyTorch Flight Recorder -->
  <g id="card-flight-recorder">
    <rect x="40" y="115" width="740" height="325" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    
    <!-- Icon 1: Flight recorder / Black box circular log (56px, stroke 4, green) -->
    <g transform="translate(65, 140)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="48" height="48" rx="8"/>
      <circle cx="28" cy="28" r="14"/>
      <polyline points="28,20 28,28 34,28"/>
      <circle cx="28" cy="28" r="3" fill="#207448"/>
    </g>

    <text x="140" y="176" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan font-size="30" font-weight="bold" fill="#207448">PyTorch flight recorder: </tspan>
      <tspan>a ring buffer</tspan>
      <tspan x="65" dy="48">(fixed-size log that overwrites oldest entries) of</tspan>
      <tspan x="65" dy="38">recent collectives kept on every rank; after a</tspan>
      <tspan x="65" dy="38">timeout or hang you can see which rank was stuck</tspan>
      <tspan x="65" dy="38">on which collective, instead of a crash message</tspan>
      <tspan x="65" dy="38">that does not say</tspan>
    </text>
  </g>

  <!-- Card 2: NCCL RAS -->
  <g id="card-nccl-ras">
    <rect x="820" y="115" width="740" height="325" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    
    <!-- Icon 2: Service / Heartbeat Network Node (56px, stroke 4, green) -->
    <g transform="translate(845, 140)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <path d="M 12 28 L 20 28 L 25 18 L 31 38 L 36 28 L 44 28"/>
    </g>

    <text x="920" y="176" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan font-size="30" font-weight="bold" fill="#207448">NCCL RAS </tspan>
      <tspan>(reliability, availability</tspan>
      <tspan x="845" dy="48">and serviceability), available from NCCL 2.24: while</tspan>
      <tspan x="845" dy="38">a job runs the <tspan font-family="monospace">ncclras</tspan> client connects to the RAS</tspan>
      <tspan x="845" dy="38">port on a node, 28028 by default, and prints which</tspan>
      <tspan x="845" dy="38">ranks and nodes NCCL considers alive or</tspan>
      <tspan x="845" dy="38">unresponsive</tspan>
    </text>
  </g>

  <!-- ==================== COMBINED FLOW CONTAINER ==================== -->
  <g id="combined-flow">
    <!-- Outer container box -->
    <rect x="40" y="475" width="1520" height="445" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>

    <!-- Process / Workflow Icon (56px, stroke 4, green) -->
    <g transform="translate(65, 498)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="18" cy="18" r="8"/>
      <circle cx="38" cy="38" r="8"/>
      <path d="M 24 24 L 32 32"/>
      <circle cx="38" cy="18" r="4"/>
      <circle cx="18" cy="38" r="4"/>
    </g>

    <!-- Top Flow Step: Timeouts & Environment variables (Orange outline for primary lever) -->
    <rect x="135" y="495" width="1395" height="195" rx="10" fill="#fff9f2" stroke="#db8129" stroke-width="3"/>
    
    <!-- Clock / Timer Icon inside the timeout step -->
    <g transform="translate(155, 515)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="20" cy="20" r="16"/>
      <polyline points="20,10 20,20 28,24"/>
    </g>

    <!-- Bottom Left Flow Step: Flight recorder dump per rank (aligned under Card 1) -->
    <rect x="65" y="715" width="700" height="175" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <g transform="translate(90, 750)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 4 L 26 4 L 36 14 L 36 44 L 6 44 Z"/>
      <polyline points="26,4 26,14 36,14"/>
      <line x1="14" y1="24" x2="28" y2="24"/>
      <line x1="14" y1="32" x2="28" y2="32"/>
    </g>

    <!-- Bottom Right Flow Step: ncclras live connection (aligned under Card 2) -->
    <rect x="835" y="715" width="700" height="175" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <g transform="translate(860, 750)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="40" height="32" rx="4"/>
      <polyline points="12,18 18,22 12,26"/>
      <line x1="22" y1="26" x2="30" y2="26"/>
    </g>

    <!-- Label 4: Combined flow text spanning all steps -->
    <text x="215" y="542" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan font-size="30" font-weight="bold" fill="#db8129">timeouts turn a hang into a crash; </tspan>
      <tspan>set </tspan>
      <tspan font-family="monospace">TORCH_NCCL_ASYNC_ERROR_HANDLING=1, </tspan>
      <tspan x="215" dy="48" font-family="monospace">TORCH_NCCL_ENABLE_MONITORING=1, </tspan>
      <tspan font-family="monospace">TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC; </tspan>
      <tspan x="145" y="785" font-size="26" font-weight="bold" fill="#207448">then read the flight recorder </tspan>
      <tspan x="145" y="828" font-size="26" font-weight="bold" fill="#207448">dump per rank; </tspan>
      <tspan x="915" y="785" font-size="26" font-weight="bold" fill="#207448">use <tspan font-family="monospace">ncclras</tspan> while the job </tspan>
      <tspan x="915" y="828" font-size="26" font-weight="bold" fill="#207448">is still hanging</tspan>
    </text>
  </g>
</svg>"""

with open("test_flight_recorder.svg", "w") as f:
    f.write(svg_candidate)

root = ET.fromstring(svg_candidate)

# Check title and desc
assert root[0].tag.endswith('title')
assert root[1].tag.endswith('desc')
print("Title and desc: PASS")

# Check dimensions
assert root.attrib['width'] == "1600"
assert root.attrib['height'] == "960"
assert root.attrib['viewBox'] == "0 0 1600 960"
print("Dimensions: PASS")

# Extract texts
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = " ".join("".join(elem.itertext()).split())
    fs = float(elem.attrib.get('font-size', '0'))
    assert fs >= 24, f"Text font size {fs} < 24"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = float(tsp.attrib.get('font-size', fs))
        assert tfs >= 24, f"Tspan font size {tfs} < 24"
    text_elements.append(full_text)

print(f"Total <text> elements: {len(text_elements)}")
for i, t in enumerate(text_elements, 1):
    print(f"  {i}. '{t}'")

# Expected labels
expected_labels = [
    "Two tools that say which rank is stuck",
    "PyTorch flight recorder: a ring buffer (fixed-size log that overwrites oldest entries) of recent collectives kept on every rank; after a timeout or hang you can see which rank was stuck on which collective, instead of a crash message that does not say",
    "NCCL RAS (reliability, availability and serviceability), available from NCCL 2.24: while a job runs the ncclras client connects to the RAS port on a node, 28028 by default, and prints which ranks and nodes NCCL considers alive or unresponsive",
    "timeouts turn a hang into a crash; set TORCH_NCCL_ASYNC_ERROR_HANDLING=1, TORCH_NCCL_ENABLE_MONITORING=1, TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC; then read the flight recorder dump per rank; use ncclras while the job is still hanging"
]

assert len(text_elements) == len(expected_labels), f"Count mismatch: {len(text_elements)} != {len(expected_labels)}"
for exp in expected_labels:
    cnt = text_elements.count(exp)
    assert cnt == 1, f"Expected '{exp}' count 1, got {cnt}"

print("All expected labels match EXACTLY once!")

# Check banned words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in text_elements:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'"

print("No forbidden words: PASS")

# Check orange count
orange_matches = re.findall(r'#db8129', svg_candidate, re.IGNORECASE)
print(f"Orange occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Orange count {len(orange_matches)} out of bounds"

# Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows: {total_arrows}")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

print("ALL TESTS PASSED WITH 100% SUCCESS!")
