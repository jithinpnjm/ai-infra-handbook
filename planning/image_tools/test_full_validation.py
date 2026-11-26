import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>Why a pod takes exactly 30 seconds to die</title>
  <desc>Infographic showing how a container without a SIGTERM handler ignores the termination signal in its PID namespace and waits the entire 30-second grace period until SIGKILL, whereas a container with a handler checkpoints and exits early.</desc>

  <defs>
    <!-- Arrowhead Green (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
    <!-- Arrowhead Red (18px) -->
    <marker id="arrow-red" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#c53030" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="56" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Why a pod takes exactly 30 seconds to die</text>

  <!-- ==================== TOP EVENT: T+0 kubelet sends SIGTERM ==================== -->
  <g id="top-event">
    <rect x="40" y="88" width="1520" height="92" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Signal / Transmission Tower Icon (56px, stroke 4) -->
    <g transform="translate(68, 106)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 8 L 28 50 M 14 50 L 42 50 M 18 28 L 38 28" />
      <path d="M 16 16 A 16 16 0 0 0 16 40" />
      <path d="M 40 16 A 16 16 0 0 1 40 40" />
      <path d="M 10 10 A 24 24 0 0 0 10 46" />
      <path d="M 46 10 A 24 24 0 0 1 46 46" />
    </g>
    <!-- Text: kubelet sends SIGTERM to PID 1 (after preStop) -->
    <text x="145" y="146" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">kubelet sends SIGTERM to PID 1 (after preStop)</text>
  </g>

  <!-- ==================== LANE A: PID 1 with no SIGTERM handler ==================== -->
  <g id="lane-a">
    <!-- Lane Container -->
    <rect x="40" y="206" width="740" height="674" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Lane A Header Icon: Process / Terminal Shell Icon (56px) -->
    <g transform="translate(68, 226)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="40" rx="6" />
      <polyline points="14,22 22,28 14,34" />
      <line x1="26" y1="34" x2="38" y2="34" />
    </g>
    <!-- Lane A Header Title (28px bold) -->
    <text x="145" y="252" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan x="145" dy="0">PID 1 is </tspan><tspan font-family="ui-monospace, monospace">/bin/sh</tspan><tspan> or a process </tspan>
      <tspan x="145" dy="36">with no SIGTERM handler</tspan>
    </text>

    <!-- Step A1: the kernel ignores signals to PID 1 in a PID namespace unless a handler is registered -->
    <g id="lane-a-step1">
      <rect x="65" y="328" width="690" height="124" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Kernel Shield Icon (56px) -->
      <g transform="translate(85, 362)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 28 6 L 48 14 V 30 C 48 44 28 52 28 52 C 28 52 8 44 8 30 V 14 Z" />
        <line x1="18" y1="20" x2="38" y2="38" />
      </g>
      <text x="165" y="370" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
        <tspan x="165" dy="0">the kernel ignores signals to PID 1 </tspan>
        <tspan x="165" dy="28">in a PID namespace unless a </tspan>
        <tspan x="165" dy="28">handler is registered</tspan>
      </text>
    </g>

    <!-- Arrow A1 -> A2 -->
    <line x1="410" y1="452" x2="410" y2="482" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- Step A2: nothing happens for the whole terminationGracePeriodSeconds (Orange Highlight) -->
    <g id="lane-a-step2">
      <rect x="65" y="482" width="690" height="114" rx="12" fill="#fff9f2" stroke="#db8129" stroke-width="3.5" />
      <!-- Timer / Clock Icon (56px) in Orange -->
      <g transform="translate(85, 511)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22" />
        <polyline points="28,14 28,28 40,28" />
        <line x1="28" y1="2" x2="28" y2="6" />
      </g>
      <text x="165" y="530" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">
        <tspan x="165" dy="0">nothing happens for the whole </tspan>
        <tspan x="165" dy="34" font-family="ui-monospace, monospace" fill="#db8129">terminationGracePeriodSeconds</tspan>
      </text>
    </g>

    <!-- Arrow A2 -> A3 -->
    <line x1="410" y1="596" x2="410" y2="626" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- Step A3: SIGKILL, which the kernel never ignores -->
    <g id="lane-a-step3">
      <rect x="65" y="626" width="690" height="104" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Lightning Bolt / Forced Action Icon (56px) -->
      <g transform="translate(85, 650)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="32,4 12,30 26,30 22,52 44,22 30,22" />
      </g>
      <text x="165" y="670" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#303a36">
        <tspan x="165" dy="0" font-family="ui-monospace, monospace">SIGKILL</tspan><tspan>, which the kernel </tspan>
        <tspan x="165" dy="34">never ignores</tspan>
      </text>
    </g>

    <!-- Arrow A3 -> A4 -->
    <line x1="410" y1="730" x2="410" y2="760" stroke="#c53030" stroke-width="3.5" marker-end="url(#arrow-red)" />

    <!-- Step A4: pod takes 30 s to die (Red) -->
    <g id="lane-a-step4">
      <rect x="65" y="760" width="690" height="100" rx="12" fill="#fdf4f4" stroke="#c53030" stroke-width="3" />
      <!-- Tombstone / Stop Circle Icon (56px) in Red -->
      <g transform="translate(85, 782)" stroke="#c53030" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22" />
        <line x1="18" y1="18" x2="38" y2="38" />
        <line x1="38" y1="18" x2="18" y2="38" />
      </g>
      <text x="165" y="822" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#c53030">pod takes 30 s to die</text>
    </g>
  </g>

  <!-- ==================== LANE B: PID 1 registers a SIGTERM handler ==================== -->
  <g id="lane-b">
    <!-- Lane Container -->
    <rect x="820" y="206" width="740" height="674" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Lane B Header Icon: Process with Shield Check Icon (56px) -->
    <g transform="translate(848, 226)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="40" rx="6" />
      <polyline points="16,28 24,36 40,20" />
    </g>
    <!-- Lane B Header Title (30px bold) -->
    <text x="925" y="264" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">PID 1 registers a SIGTERM handler</text>

    <!-- Step B1: saves checkpoint or drains, exits 0 -->
    <g id="lane-b-step1">
      <rect x="845" y="328" width="690" height="124" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Disk Cylinder / Storage Save Icon (56px) -->
      <g transform="translate(865, 362)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <ellipse cx="28" cy="14" rx="20" ry="8" />
        <path d="M 8 14 V 42 C 8 46.4 17 50 28 50 C 39 50 48 46.4 48 42 V 14" />
        <path d="M 8 28 C 8 32.4 17 36 28 36 C 39 36 48 32.4 48 28" />
      </g>
      <text x="945" y="380" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#303a36">
        <tspan x="945" dy="0">saves checkpoint or drains, </tspan>
        <tspan x="945" dy="36" font-family="ui-monospace, monospace">exits 0</tspan>
      </text>
    </g>

    <!-- Arrow B1 -> B2 -->
    <line x1="1190" y1="452" x2="1190" y2="500" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- Step B2: pod ends early (Green) -->
    <g id="lane-b-step2">
      <rect x="845" y="500" width="690" height="114" rx="12" fill="#ffffff" stroke="#207448" stroke-width="3" />
      <!-- Success Check Circle Icon (56px) in Green -->
      <g transform="translate(865, 529)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22" />
        <polyline points="18,28 25,35 38,20" />
      </g>
      <text x="945" y="568" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="#207448">pod ends early</text>
    </g>
  </g>

  <!-- ==================== SIDE NOTE ==================== -->
  <g id="side-note">
    <rect x="40" y="906" width="1520" height="130" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Info / Lightbulb Icon (56px) -->
    <g transform="translate(68, 943)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="24" r="16" />
      <path d="M 20 40 H 36 M 23 46 H 33" />
      <line x1="28" y1="2" x2="28" y2="6" />
      <line x1="12" y1="8" x2="15" y2="11" />
      <line x1="44" y1="8" x2="41" y2="11" />
    </g>
    <!-- Text: shell-form entrypoint can swallow SIGTERM; for training treat SIGTERM as checkpoint now and set the grace period from a measured checkpoint time plus margin -->
    <text x="145" y="960" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="145" dy="0">shell-form entrypoint can swallow SIGTERM; for training treat SIGTERM as checkpoint now </tspan>
      <tspan x="145" dy="34">and set the grace period from a measured checkpoint time plus margin</tspan>
    </text>
  </g>
</svg>"""

root = ET.fromstring(svg_content)

# Test 1: title & desc
assert root[0].tag.endswith('title')
assert root[1].tag.endswith('desc')

# Test 2: dimensions
assert root.attrib['width'] == '1600'
assert root.attrib['height'] == '1080'
assert root.attrib['viewBox'] == '0 0 1600 1080'

# Test 3: text elements
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib['font-size'])
    assert fs >= 24
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        if 'font-size' in tsp.attrib:
            assert float(tsp.attrib['font-size']) >= 24
    text_elements.append((full_text, fs))

expected_labels = [
    "Why a pod takes exactly 30 seconds to die",
    "kubelet sends SIGTERM to PID 1 (after preStop)",
    "PID 1 is /bin/sh or a process with no SIGTERM handler",
    "the kernel ignores signals to PID 1 in a PID namespace unless a handler is registered",
    "nothing happens for the whole terminationGracePeriodSeconds",
    "SIGKILL, which the kernel never ignores",
    "pod takes 30 s to die",
    "PID 1 registers a SIGTERM handler",
    "saves checkpoint or drains, exits 0",
    "pod ends early",
    "shell-form entrypoint can swallow SIGTERM; for training treat SIGTERM as checkpoint now and set the grace period from a measured checkpoint time plus margin"
]

found_texts = [t for t, fs in text_elements]
for exp in expected_labels:
    assert found_texts.count(exp) == 1, f"Missing or duplicate: {exp}"

extras = [t for t in found_texts if t not in expected_labels]
assert len(extras) == 0, f"Extras: {extras}"
assert len(found_texts) == len(expected_labels)

# Forbidden
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words

# Arrows
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
assert len(lines) + len(paths) == 4

print("PERFECT VALIDATION: ALL TESTS PASSED!")
