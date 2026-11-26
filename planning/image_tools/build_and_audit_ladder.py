import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

# Let's write the SVG builder and validator
svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>The TTFT page fires: five checks in order</title>
  <desc>Ladder for the alert GatewayTTFTBurnFast on one model: five checks in order from gateway slow share, engine queue, memory cache usage, preemptions, to TTFT versus queue time comparison, with immediate mitigation priority.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="62" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The TTFT page fires: five checks in order</text>

  <!-- ==================== LADDER CONTAINER (LEFT COLUMN) ==================== -->
  <rect x="40" y="95" width="1020" height="1065" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

  <!-- Ladder Container Header Card -->
  <rect x="65" y="118" width="970" height="68" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <g transform="translate(85, 124)" stroke="#207448" stroke-width="4" stroke-linecap="round" fill="none">
    <line x1="16" y1="8" x2="16" y2="48"/>
    <line x1="40" y1="8" x2="40" y2="48"/>
    <line x1="16" y1="16" x2="40" y2="16"/>
    <line x1="16" y1="26" x2="40" y2="26"/>
    <line x1="16" y1="36" x2="40" y2="36"/>
    <line x1="16" y1="44" x2="40" y2="44"/>
  </g>
  <text x="155" y="161" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Ladder for the alert GatewayTTFTBurnFast on one model.</text>

  <!-- Step 1: Gateway check -->
  <g id="step-1">
    <rect x="65" y="206" width="970" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <!-- Number circle 1 -->
    <circle cx="110" cy="281" r="24" fill="#207448"/>
    <text x="110" y="289" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
    <!-- Gateway Icon (56x56) -->
    <g transform="translate(150, 253)" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <rect x="8" y="10" width="40" height="38" rx="6"/>
      <path d="M 18 48 L 18 28 Q 28 20 38 28 L 38 48"/>
      <circle cx="28" cy="19" r="2" fill="#207448"/>
    </g>
    <!-- Step 1 Text -->
    <text x="235" y="254" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="235" dy="0" font-weight="bold" fill="#207448">gateway: </tspan><tspan>is the slow share rising for all tenants or</tspan>
      <tspan x="235" dy="36">one? run the per-tenant ratio; one tenant means look</tspan>
      <tspan x="235" dy="36">for a burst of long prompts</tspan>
    </text>
  </g>

  <!-- Step 2: Engine queue -->
  <g id="step-2">
    <rect x="65" y="376" width="970" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <!-- Number circle 2 -->
    <circle cx="110" cy="451" r="24" fill="#207448"/>
    <text x="110" y="459" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
    <!-- Engine Queue Icon (56x56) -->
    <g transform="translate(150, 423)" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <rect x="6" y="12" width="44" height="32" rx="6"/>
      <line x1="18" y1="12" x2="18" y2="44"/>
      <line x1="30" y1="12" x2="30" y2="44"/>
      <line x1="42" y1="12" x2="42" y2="44"/>
      <circle cx="12" cy="28" r="2.5" fill="#207448"/>
      <circle cx="24" cy="28" r="2.5" fill="#207448"/>
      <circle cx="36" cy="28" r="2.5" fill="#207448"/>
    </g>
    <!-- Step 2 Text -->
    <text x="235" y="424" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="235" dy="0" font-weight="bold" fill="#207448">engine queue: </tspan><tspan font-family="monospace">sum by (model_name)</tspan>
      <tspan x="235" dy="36" font-family="monospace">(vllm:num_requests_waiting); </tspan><tspan font-family="sans-serif">growing means requests</tspan>
      <tspan x="235" dy="36">wait before prefill</tspan>
    </text>
  </g>

  <!-- Step 3: Memory KV cache usage -->
  <g id="step-3">
    <rect x="65" y="546" width="970" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <!-- Number circle 3 -->
    <circle cx="110" cy="621" r="24" fill="#207448"/>
    <text x="110" y="629" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
    <!-- Memory Chip Icon (56x56) -->
    <g transform="translate(150, 593)" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <rect x="10" y="10" width="36" height="36" rx="6"/>
      <line x1="10" y1="28" x2="46" y2="28" stroke-width="3"/>
      <line x1="28" y1="10" x2="28" y2="46" stroke-width="3"/>
      <line x1="18" y1="4" x2="18" y2="10" stroke-width="3"/>
      <line x1="38" y1="4" x2="38" y2="10" stroke-width="3"/>
      <line x1="18" y1="46" x2="18" y2="52" stroke-width="3"/>
      <line x1="38" y1="46" x2="38" y2="52" stroke-width="3"/>
      <line x1="4" y1="18" x2="10" y2="18" stroke-width="3"/>
      <line x1="4" y1="38" x2="10" y2="38" stroke-width="3"/>
      <line x1="46" y1="18" x2="52" y2="18" stroke-width="3"/>
      <line x1="46" y1="38" x2="52" y2="38" stroke-width="3"/>
    </g>
    <!-- Step 3 Text -->
    <text x="235" y="594" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="235" dy="0" font-weight="bold" fill="#207448">memory: </tspan><tspan font-family="monospace">max by (model_name)</tspan>
      <tspan x="235" dy="36" font-family="monospace">(vllm:kv_cache_usage_perc); </tspan><tspan font-family="sans-serif">near 1 means the cache</tspan>
      <tspan x="235" dy="36">is full and new requests wait for blocks</tspan>
    </text>
  </g>

  <!-- Step 4: Preemptions -->
  <g id="step-4">
    <rect x="65" y="716" width="970" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <!-- Number circle 4 -->
    <circle cx="110" cy="791" r="24" fill="#207448"/>
    <text x="110" y="799" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
    <!-- Preemption Recycle Icon (56x56) -->
    <g transform="translate(150, 763)" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <path d="M 12 28 A 16 16 0 1 1 28 44"/>
      <polyline points="20,44 28,44 28,36"/>
      <line x1="22" y1="20" x2="34" y2="32"/>
      <line x1="34" y1="20" x2="22" y2="32"/>
    </g>
    <!-- Step 4 Text -->
    <text x="235" y="764" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="235" dy="0" font-weight="bold" fill="#207448">preemptions: </tspan><tspan font-family="monospace">rate(vllm:num_preemptions_total[10m]);</tspan>
      <tspan x="235" dy="36">non-zero means running requests were evicted and</tspan>
      <tspan x="235" dy="36">restarted</tspan>
    </text>
  </g>

  <!-- Step 5: TTFT vs Queue Time Comparison -->
  <g id="step-5">
    <rect x="65" y="886" width="970" height="250" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <!-- Number circle 5 -->
    <circle cx="110" cy="1011" r="24" fill="#207448"/>
    <text x="110" y="1019" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
    <!-- Timer / Balance Scale Icon (56x56) -->
    <g transform="translate(150, 983)" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <circle cx="28" cy="28" r="22"/>
      <polyline points="28,14 28,28 38,28"/>
      <line x1="16" y1="8" x2="40" y2="8" stroke-width="3"/>
    </g>
    <!-- Step 5 Text -->
    <text x="235" y="924" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="235" dy="0">compare </tspan><tspan font-family="monospace">vllm:time_to_first_token_seconds</tspan><tspan> with</tspan>
      <tspan x="235" dy="36" font-family="monospace">vllm:request_queue_time_seconds: </tspan><tspan font-family="sans-serif">if queue time</tspan>
      <tspan x="235" dy="36">explains most of TTFT the fix is capacity or routing;</tspan>
      <tspan x="235" dy="36">if prefill time grew look at prompt length mix and</tspan>
      <tspan x="235" dy="36">the prefix cache</tspan>
    </text>
  </g>

  <!-- ==================== SIDE BOX (RIGHT COLUMN) ==================== -->
  <!-- Single most important item highlighted in orange #db8129 -->
  <g id="side-box">
    <rect x="1100" y="95" width="460" height="1065" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3"/>

    <!-- Orange Shield / First-Aid Mitigation Icon (56x56) -->
    <g transform="translate(1302, 140)" stroke="#db8129" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <path d="M 28 6 L 48 14 L 48 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 L 8 14 Z"/>
      <line x1="28" y1="18" x2="28" y2="38"/>
      <line x1="18" y1="28" x2="38" y2="28"/>
    </g>

    <!-- Side Box Card Interior Panel -->
    <rect x="1125" y="225" width="410" height="420" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>

    <!-- Side Box Text -->
    <text x="1145" y="275" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1145" dy="0" font-weight="bold" fill="#db8129">mitigate before the</tspan>
      <tspan x="1145" dy="38" font-weight="bold" fill="#db8129">root cause: </tspan><tspan font-weight="bold">add replicas,</tspan>
      <tspan x="1145" dy="38">shed a tenant that exceeded</tspan>
      <tspan x="1145" dy="38">its quota, or route away from</tspan>
      <tspan x="1145" dy="38">the bad replica</tspan>
    </text>
  </g>
</svg>'''

pathlib.Path("test_candidate_ladder.svg").write_text(svg_code)
print("Saved test_candidate_ladder.svg successfully")

tree = ET.parse("test_candidate_ladder.svg")
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
assert width == "1600"
vb = [float(x) for x in viewBox.split()]
assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
assert 900 <= vb[3] <= 1200
assert int(height) == int(vb[3])

# 3. Check text elements
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    assert fs >= 24, f"Text font size {fs} < 24! Text: '{full_text}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24! in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"\n3. Total text elements: {len(text_elements)}")
found_texts = [t for t, fs in text_elements]
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# Expected labels
expected_labels = [
    "The TTFT page fires: five checks in order",
    "Ladder for the alert GatewayTTFTBurnFast on one model.",
    "gateway: is the slow share rising for all tenants or one? run the per-tenant ratio; one tenant means look for a burst of long prompts",
    "engine queue: sum by (model_name) (vllm:num_requests_waiting); growing means requests wait before prefill",
    "memory: max by (model_name) (vllm:kv_cache_usage_perc); near 1 means the cache is full and new requests wait for blocks",
    "preemptions: rate(vllm:num_preemptions_total[10m]); non-zero means running requests were evicted and restarted",
    "compare vllm:time_to_first_token_seconds with vllm:request_queue_time_seconds: if queue time explains most of TTFT the fix is capacity or routing; if prefill time grew look at prompt length mix and the prefix cache",
    "mitigate before the root cause: add replicas, shed a tenant that exceeded its quota, or route away from the bad replica"
]

step_numbers = {"1", "2", "3", "4", "5"}

print(f"\n4. Checking {len(expected_labels)} expected labels against found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:50]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts (non-step): {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

for num in step_numbers:
    cnt = found_texts.count(num)
    assert cnt == 1, f"Step number {num} count is {cnt} != 1!"

print("  [PASS] Every label and step number present exactly once, no extras.")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("  [PASS] No forbidden words found!")

# 6. Check orange count
orange_matches = re.findall(r'#db8129', svg_code, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
print("  [PASS] Orange used only for single important transition/item!")

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"
print("  [PASS] Exactly 0 arrows!")

# 8. Check external resources: no <image>, <script>, external fonts
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert '@import' not in svg_code, "No external fonts allowed"
print("  [PASS] No external assets or scripts!")

# 9. Colors present
assert "#f5f8f5" in svg_code
assert "#303a36" in svg_code
assert "#207448" in svg_code
assert "#e8f1ea" in svg_code
assert "#db8129" in svg_code
print("  [PASS] All required palette colors present!")
print("\nALL 9 AUDIT CHECKS PASSED PERFECTLY!")

