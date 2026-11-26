import re
import xml.etree.ElementTree as ET
import subprocess
import pathlib

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Is the cheaper GPU cheaper per token?</title>
  <desc>Side-by-side worked comparison of NVIDIA H100 versus L40S for Qwen3-8B BF16 inference at batch 32 showing throughput, latency, and cost per million tokens.</desc>

  <defs>
    <!-- Icon 1: GPU Chip (56x56) -->
    <g id="icon-chip" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="6"/>
      <rect x="18" y="18" width="20" height="20" rx="3"/>
      <line x1="18" y1="2" x2="18" y2="8"/>
      <line x1="28" y1="2" x2="28" y2="8"/>
      <line x1="38" y1="2" x2="38" y2="8"/>
      <line x1="18" y1="48" x2="18" y2="54"/>
      <line x1="28" y1="48" x2="28" y2="54"/>
      <line x1="38" y1="48" x2="38" y2="54"/>
      <line x1="2" y1="18" x2="8" y2="18"/>
      <line x1="2" y1="28" x2="8" y2="28"/>
      <line x1="2" y1="38" x2="8" y2="38"/>
      <line x1="48" y1="18" x2="54" y2="18"/>
      <line x1="48" y1="28" x2="54" y2="28"/>
      <line x1="48" y1="38" x2="54" y2="38"/>
    </g>

    <!-- Icon 2: High Bandwidth Memory / Bus (56x56) -->
    <g id="icon-bandwidth" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="14" width="44" height="28" rx="4"/>
      <line x1="15" y1="14" x2="15" y2="42"/>
      <line x1="28" y1="14" x2="28" y2="42"/>
      <line x1="41" y1="14" x2="41" y2="42"/>
      <path d="M 10 6 L 28 6 L 46 6"/>
      <polyline points="22,2 28,6 22,10"/>
      <path d="M 10 50 L 28 50 L 46 50"/>
      <polyline points="34,46 28,50 34,54"/>
    </g>

    <!-- Icon 3: Speedometer / Request Rate (56x56) -->
    <g id="icon-gauge" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 42 A 22 22 0 1 1 48 42"/>
      <circle cx="28" cy="38" r="4" fill="#207448"/>
      <line x1="28" y1="38" x2="40" y2="22"/>
      <line x1="12" y1="28" x2="16" y2="28"/>
      <line x1="28" y1="12" x2="28" y2="16"/>
      <line x1="44" y1="28" x2="40" y2="28"/>
    </g>

    <!-- Icon 4: Token Stream / Output Wave (56x56) -->
    <g id="icon-tokens" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="20" height="20" rx="3"/>
      <rect x="30" y="10" width="20" height="20" rx="3"/>
      <rect x="18" y="26" width="20" height="20" rx="3"/>
      <path d="M 12 36 L 12 46 L 44 46 L 44 36"/>
    </g>

    <!-- Icon 5: Orange Best Cost Star / Badge (56x56) -->
    <g id="icon-cost-orange" fill="none" stroke="#db8129" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <circle cx="28" cy="28" r="14"/>
      <line x1="28" y1="10" x2="28" y2="14"/>
      <line x1="28" y1="42" x2="28" y2="46"/>
      <line x1="10" y1="28" x2="14" y2="28"/>
      <line x1="42" y1="28" x2="46" y2="28"/>
    </g>

    <!-- Icon 6: Stopwatch / Latency (56x56) -->
    <g id="icon-clock" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="30" r="20"/>
      <polyline points="28,18 28,30 38,30"/>
      <line x1="28" y1="4" x2="28" y2="10"/>
      <line x1="22" y1="4" x2="34" y2="4"/>
    </g>

    <!-- Icon 7: Memory Budget / Bar (56x56) -->
    <g id="icon-budget" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="12" width="44" height="32" rx="4"/>
      <line x1="22" y1="12" x2="22" y2="44"/>
      <line x1="36" y1="12" x2="36" y2="44"/>
      <rect x="10" y="18" width="8" height="20" rx="2"/>
    </g>

    <!-- Icon 8: Decode Step / Memory Fetch (56x56) -->
    <g id="icon-decode" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="44" height="16" rx="3"/>
      <rect x="6" y="30" width="44" height="16" rx="3"/>
      <polyline points="18,18 24,24 18,30"/>
      <polyline points="32,18 38,24 32,30"/>
    </g>

    <!-- Icon 9: Prefill Compute / Tensor TFLOPS (56x56) -->
    <g id="icon-prefill" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="30,4 12,30 26,30 20,52 42,22 28,22"/>
    </g>

    <!-- Icon 10: Calculation / Cost (56x56) -->
    <g id="icon-calc" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="6" width="36" height="44" rx="4"/>
      <rect x="16" y="12" width="24" height="8" rx="2"/>
      <line x1="16" y1="26" x2="22" y2="26"/>
      <line x1="28" y1="26" x2="34" y2="26"/>
      <line x1="16" y1="34" x2="22" y2="34"/>
      <line x1="28" y1="34" x2="34" y2="34"/>
      <line x1="16" y1="42" x2="34" y2="42"/>
    </g>

    <!-- Icon 11: Verdict Shield (White, 56x56) -->
    <g id="icon-shield" fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 42 28 52 28 52 C 28 52 8 42 8 28 V 14 Z"/>
      <polyline points="20,28 26,34 38,20"/>
    </g>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Diagram Title -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Is the cheaper GPU cheaper per token?</text>

  <!-- Subtitle Context Note -->
  <text x="800" y="100" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">Side-by-side worked comparison for Qwen3-8B BF16 at batch 32 with list prices fetched 2026-11-09.</text>

  <!-- ==================== LEFT COLUMN: H100 ==================== -->
  <g id="column-h100">
    <!-- Outer Container -->
    <rect x="60" y="135" width="710" height="910" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Column Header -->
    <rect x="80" y="155" width="670" height="75" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-chip" x="100" y="164"/>
    <text x="180" y="202" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">H100 at $4.50 per GPU-hour</text>

    <!-- Card H1: Hardware Specs -->
    <rect x="80" y="245" width="670" height="110" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-bandwidth" x="105" y="272"/>
    <text x="185" y="310" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">80 GB, 3.35 TB/s</text>

    <!-- Card H2: Request Throughput -->
    <rect x="80" y="400" width="670" height="110" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-gauge" x="105" y="427"/>
    <text x="185" y="465" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">4.66 requests per second</text>

    <!-- Card H3: Token Throughput -->
    <rect x="80" y="555" width="670" height="110" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-tokens" x="105" y="582"/>
    <text x="185" y="620" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">about 2,330 output tokens per second</text>

    <!-- Card H4: Cost per Token (Single Orange Highlighted Item) -->
    <rect x="80" y="710" width="670" height="160" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="3.5"/>
    <use href="#icon-cost-orange" x="105" y="762"/>
    <text x="185" y="802" font-family="sans-serif" font-size="28" font-weight="bold" fill="#db8129">$0.54 per million output tokens</text>

    <!-- Card H5: Latency -->
    <rect x="80" y="915" width="670" height="110" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-clock" x="105" y="942"/>
    <text x="185" y="980" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">latency about 6.9 s per request</text>
  </g>

  <!-- ==================== RIGHT COLUMN: L40S ==================== -->
  <g id="column-l40s">
    <!-- Outer Container -->
    <rect x="830" y="135" width="710" height="910" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Column Header -->
    <rect x="850" y="155" width="670" height="75" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-chip" x="870" y="164"/>
    <text x="950" y="202" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">L40S at $1.55 per GPU-hour</text>

    <!-- Card L1: Hardware Specs -->
    <rect x="850" y="245" width="670" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-bandwidth" x="870" y="258"/>
    <text x="942" y="280" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="942" dy="0">48 GB at 864 GB/s and</tspan>
      <tspan x="942" dy="28">about 362 dense BF16 TFLOPS</tspan>
    </text>

    <!-- Card L2: Memory Budget -->
    <rect x="850" y="342" width="670" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-budget" x="870" y="355"/>
    <text x="942" y="377" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="942" dy="0">budget 48 x 0.9 - 16.4 - 5 =</tspan>
      <tspan x="942" dy="28">21.8 GB = 59 requests</tspan>
    </text>

    <!-- Card L3: Decode Step -->
    <rect x="850" y="439" width="670" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-decode" x="870" y="452"/>
    <text x="942" y="474" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="942" dy="0">decode step (16.4 + 11.796) / 864 =</tspan>
      <tspan x="942" dy="28">32.6 ms so 981 tokens per second</tspan>
    </text>

    <!-- Card L4: Prefill Step -->
    <rect x="850" y="536" width="670" height="102" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-prefill" x="870" y="559"/>
    <text x="942" y="567" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="942" dy="0">prefill 362e12 x 0.4 / 16.4e9 =</tspan>
      <tspan x="942" dy="28">8,829 tokens per second so</tspan>
      <tspan x="942" dy="28">0.2265 s per prompt</tspan>
    </text>

    <!-- Card L5: GPU Seconds per Request -->
    <rect x="850" y="653" width="670" height="102" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-gauge" x="870" y="676"/>
    <text x="942" y="684" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="942" dy="0">GPU seconds per request</tspan>
      <tspan x="942" dy="28">0.2265 + 0.5097 = 0.736 so</tspan>
      <tspan x="942" dy="28">1.36 requests per second</tspan>
    </text>

    <!-- Card L6: Token Throughput -->
    <rect x="850" y="770" width="670" height="72" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-tokens" x="870" y="778"/>
    <text x="942" y="815" font-family="sans-serif" font-size="24" fill="#303a36">about 679 output tokens per second</text>

    <!-- Card L7: Cost per Token Calculation -->
    <rect x="850" y="857" width="670" height="82" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-calc" x="870" y="870"/>
    <text x="942" y="892" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="942" dy="0">$1.55 / (679 x 3,600) x 1e6 =</tspan>
      <tspan x="942" dy="28">$0.63 per million</tspan>
    </text>

    <!-- Card L8: Latency -->
    <rect x="850" y="954" width="670" height="72" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <use href="#icon-clock" x="870" y="962"/>
    <text x="942" y="999" font-family="sans-serif" font-size="24" fill="#303a36">latency about 24 s per request</text>
  </g>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="60" y="1065" width="1480" height="100" rx="14" fill="#207448"/>
    <use href="#icon-shield" x="85" y="1087"/>
    <text x="165" y="1108" font-family="sans-serif" font-size="24" fill="#ffffff">
      <tspan x="165" dy="0">the H100 costs less per token even though it costs three times more per hour:</tspan>
      <tspan x="165" dy="34">tokens per second sit in the bottom of the fraction</tspan>
    </text>
  </g>
</svg>'''

svg_file = "test_cheaper_gpu_per_token.svg"
pathlib.Path(svg_file).write_text(svg_content)
print(f"Wrote {svg_file}")

tree = ET.parse(svg_file)
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"
assert children[0].text == "Is the cheaper GPU cheaper per token?"
print("1. [PASS] <title> and <desc> are first children.")

# 2. Canvas dimensions check
width = root.attrib.get("width")
height = root.attrib.get("height")
viewBox = root.attrib.get("viewBox")
assert width == "1600"
assert height == "1200"
assert viewBox == "0 0 1600 1200"
print("2. [PASS] Canvas 1600x1200.")

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
    "Is the cheaper GPU cheaper per token?",
    "Side-by-side worked comparison for Qwen3-8B BF16 at batch 32 with list prices fetched 2026-11-09.",
    "H100 at $4.50 per GPU-hour",
    "80 GB, 3.35 TB/s",
    "4.66 requests per second",
    "about 2,330 output tokens per second",
    "$0.54 per million output tokens",
    "latency about 6.9 s per request",
    "L40S at $1.55 per GPU-hour",
    "48 GB at 864 GB/s and about 362 dense BF16 TFLOPS",
    "budget 48 x 0.9 - 16.4 - 5 = 21.8 GB = 59 requests",
    "decode step (16.4 + 11.796) / 864 = 32.6 ms so 981 tokens per second",
    "prefill 362e12 x 0.4 / 16.4e9 = 8,829 tokens per second so 0.2265 s per prompt",
    "GPU seconds per request 0.2265 + 0.5097 = 0.736 so 1.36 requests per second",
    "about 679 output tokens per second",
    "$1.55 / (679 x 3,600) x 1e6 = $0.63 per million",
    "latency about 24 s per request",
    "the H100 costs less per token even though it costs three times more per hour: tokens per second sit in the bottom of the fraction"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
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
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("4. [PASS] All 18 labels match exactly once, zero extras!")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' found in '{t}'!"
print("\n5. [PASS] Zero forbidden words found!")

# 6. Check orange count
orange_matches = re.findall(r'#db8129', svg_content, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"
print("6. [PASS] Orange used only for single winning cost item!")

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
print("7. [PASS] Zero arrows as specified by source.")

# 8. Render with Chrome headless
png_file = "/tmp/svgcheck/test_cheaper_gpu_per_token.png"
pathlib.Path("/tmp/svgcheck").mkdir(exist_ok=True)
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
res = subprocess.run([
    chrome_path,
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--window-size=1600,1200",
    f"--screenshot={png_file}",
    f"file://{pathlib.Path(svg_file).resolve()}"
], capture_output=True, text=True)
print(f"8. Chrome render exit code: {res.returncode}")
assert res.returncode == 0, f"Chrome failed: {res.stderr}"
print(f"Screenshot saved to {png_file}")
print("ALL CHECKS PASSED!")
