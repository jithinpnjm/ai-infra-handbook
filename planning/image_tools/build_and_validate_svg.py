import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>Why a worker that asks too early waits 30 seconds</title>
  <desc>Visual infographic explaining how negative DNS caching (NXDOMAIN with 30s SOA minimum) delays worker pod startup and how to prevent it.</desc>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="70" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Why a worker that asks too early waits 30 seconds</text>

  <!-- ==================== LEFT COLUMN: TIMELINE ==================== -->

  <!-- Step 1: T0 -->
  <g id="step-t0">
    <rect x="60" y="120" width="900" height="220" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Network / DNS Query Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(85, 140)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="24" r="16" />
      <line x1="39" y1="35" x2="50" y2="46" />
      <line x1="20" y1="24" x2="36" y2="24" />
      <line x1="28" y1="16" x2="28" y2="32" />
    </g>
    <text x="160" y="175" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">T0</text>
    <text x="160" y="225" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="160" dy="0">worker pod resolves trainer-0.trainer.ml before that</tspan>
      <tspan x="160" dy="37">pod exists: NXDOMAIN, cached as a negative answer</tspan>
      <tspan x="160" dy="37">(cache denial, SOA minimum 30 s)</tspan>
    </text>
  </g>

  <!-- Step 2: T0+few s -->
  <g id="step-t0-plus-few">
    <rect x="60" y="370" width="900" height="160" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Pod / Container Starting Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(85, 390)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="6" />
      <line x1="6" y1="20" x2="50" y2="20" />
      <circle cx="14" cy="14" r="2" fill="#207448" />
      <circle cx="22" cy="14" r="2" fill="#207448" />
      <polyline points="20,34 26,40 38,28" />
    </g>
    <text x="160" y="425" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">T0+few s</text>
    <text x="160" y="480" font-family="sans-serif" font-size="24" fill="#303a36">trainer-0 pod starts and its record now exists</text>
  </g>

  <!-- Step 3: Until T0+30 s (Single Orange Item: the 30s NXDOMAIN bottleneck) -->
  <g id="step-until-30">
    <rect x="60" y="560" width="900" height="200" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3" />
    <!-- Sticky Note / Blocked Clock Icon (56x56 outline, orange stroke 4) -->
    <g transform="translate(85, 580)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 38,28" />
      <line x1="12" y1="12" x2="44" y2="44" />
    </g>
    <text x="160" y="615" font-family="sans-serif" font-size="32" font-weight="bold" fill="#db8129">Until T0+30 s</text>
    <text x="160" y="670" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="160" dy="0">the worker keeps getting the cached NXDOMAIN:</tspan>
      <tspan x="160" dy="38">sticky note saying no such person</tspan>
    </text>
  </g>

  <!-- Step 4: T0+30 s -->
  <g id="step-t0-plus-30">
    <rect x="60" y="790" width="900" height="160" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Joined Nodes / Success Checkmark Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(85, 810)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="28" r="8" />
      <circle cx="40" cy="28" r="8" />
      <line x1="24" y1="28" x2="32" y2="28" />
      <path d="M 12 12 L 28 6 L 44 12" />
    </g>
    <text x="160" y="845" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">T0+30 s</text>
    <text x="160" y="900" font-family="sans-serif" font-size="24" fill="#303a36">cache entry expires, lookup succeeds, worker joins</text>
  </g>

  <!-- ==================== RIGHT COLUMN: FIX AND SIDE ==================== -->

  <!-- Fix Box -->
  <g id="box-fix">
    <rect x="1000" y="120" width="540" height="460" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Gear / Service Fix Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(1035, 145)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="10" />
      <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12 12 L 17 17 M 39 39 L 44 44 M 12 44 L 17 39 M 39 17 L 44 12" />
    </g>
    <text x="1035" y="235" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1035" dy="0">workers retry with backoff and</tspan>
      <tspan x="1035" dy="35">bounded timeouts;</tspan>
      <tspan x="1035" dy="35">applications avoid caching</tspan>
      <tspan x="1035" dy="35">failures; headless Service with</tspan>
      <tspan x="1035" dy="35">publishNotReadyAddresses true</tspan>
      <tspan x="1035" dy="35">so peers resolve before ready;</tspan>
      <tspan x="1035" dy="35">stagger startup</tspan>
    </text>
  </g>

  <!-- Side Box -->
  <g id="box-side">
    <rect x="1000" y="610" width="540" height="420" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Shield / Security Manager Lock Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(1035, 635)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 40 38 48 28 52 C 18 48 8 40 8 28 V 14 Z" />
      <circle cx="28" cy="26" r="4" />
      <line x1="28" y1="30" x2="28" y2="36" />
    </g>
    <text x="1035" y="725" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1035" dy="0">JVM caches successful lookups</tspan>
      <tspan x="1035" dy="35">indefinitely with a security</tspan>
      <tspan x="1035" dy="35">manager, 30 s without one;</tspan>
      <tspan x="1035" dy="35">set TTL properties so</tspan>
      <tspan x="1035" dy="35">clients drop old IPs</tspan>
      <tspan x="1035" dy="35">after failover</tspan>
    </text>
  </g>
</svg>'''

with open("candidate_test.svg", "w") as f:
    f.write(svg_content)

print("Saved candidate_test.svg. Validating...")

# Validation
root = ET.fromstring(svg_content)
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print("1. Title and desc children: PASS")

width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
assert width == "1600"
assert viewBox == "0 0 1600 1080"
assert height == "1080"
print("2. Canvas dimensions: PASS")

def get_full_text(elem):
    text = elem.text or ""
    for child in elem:
        text += get_full_text(child)
        text += child.tail or ""
    return text

text_elements = []
for t in root.iter("{http://www.w3.org/2000/svg}text"):
    content = " ".join(get_full_text(t).split())
    fs = float(t.attrib.get('font-size', '24').replace('px', ''))
    assert fs >= 24, f"Text '{content}' fs {fs} < 24!"
    text_elements.append((content, fs))

print(f"\n3. Total text elements: {len(text_elements)}")
for i, (txt, fs) in enumerate(text_elements, 1):
    print(f"  {i:2d}. [{fs}px] '{txt}'")

expected_labels = [
    "Why a worker that asks too early waits 30 seconds",
    "T0",
    "worker pod resolves trainer-0.trainer.ml before that pod exists: NXDOMAIN, cached as a negative answer (cache denial, SOA minimum 30 s)",
    "T0+few s",
    "trainer-0 pod starts and its record now exists",
    "Until T0+30 s",
    "the worker keeps getting the cached NXDOMAIN: sticky note saying no such person",
    "T0+30 s",
    "cache entry expires, lookup succeeds, worker joins",
    "workers retry with backoff and bounded timeouts; applications avoid caching failures; headless Service with publishNotReadyAddresses true so peers resolve before ready; stagger startup",
    "JVM caches successful lookups indefinitely with a security manager, 30 s without one; set TTL properties so clients drop old IPs after failover"
]

all_found = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(all_found)} found:")
all_ok = True
for exp in expected_labels:
    cnt = all_found.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
        print(f"  [FAIL] count={cnt}: '{exp}'")
    else:
        print(f"  [OK] '{exp[:40]}...'")

assert all_ok, "Some labels failed count == 1 check!"
assert len(all_found) == len(expected_labels), f"Found {len(all_found)} texts != {len(expected_labels)}"
print("4. Expected labels fidelity: PASS (All 11 match exactly once, 0 extras, 0 missing)")

# Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in all_found:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'"
print("5. Forbidden words: PASS")

# Orange count
orange_matches = re.findall(r'#db8129', svg_content, re.IGNORECASE)
print(f"6. Orange matches: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4
print("6. Orange count: PASS")

# Required colors
assert "#f5f8f5" in svg_content
assert "#303a36" in svg_content
assert "#207448" in svg_content
assert "#e8f1ea" in svg_content
assert "#db8129" in svg_content
print("7. Required palette colors: PASS")

# Arrow count
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
print("8. Arrow count (0 == 0): PASS")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
