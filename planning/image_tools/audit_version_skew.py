import re
import subprocess
import xml.etree.ElementTree as ET

svg_path = 'test_candidate_version_skew.svg'
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. First children check: <title> and <desc>
first = root[0].tag.split('}')[-1]
second = root[1].tag.split('}')[-1]
print(f"1. Children tags: <{first}>, <{second}>")
assert first == 'title', f"First child must be title, got {first}"
assert second == 'desc', f"Second child must be desc, got {second}"

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox == "0 0 1600 1200"

# 3. Text elements & font sizes
font_sizes = []
texts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = " ".join("".join(elem.itertext()).split())
    fs = float(elem.attrib.get('font-size', 0))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    texts.append(full_text)
    font_sizes.append((fs, full_text))
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"

print(f"\n3. Total text elements: {len(texts)}")
for fs, txt in font_sizes:
    print(f"   [{fs:.0f}px] '{txt[:70]}...'")

# 4. Content fidelity
expected_source_labels = [
    'Version skew during a rollout',
    'Four skew cases, each with the fix.',
    'Engine version against router',
    'Request accepted by the old version and rejected by the new in the same minute: two versions run at once during a rollout',
    'Prefix cache: different weights produce different KV values; reusing a block from old weights would feed the new model numbers it never computed, wrong answers with no error; key the prefix cache and cache-aware routing by model version so no hit crosses a version boundary',
    'Tokenizer against weights: a checkpoint with the wrong tokenizer fails quietly, garbage output and green infrastructure; the registry record makes weights, tokenizer and config one object with one version',
    'Client-facing: a user who sees both versions in one conversation may see style change midway; sticky routing by tenant or session during the canary sends one user back to the same version every time; this is the difference between a canary and an A/B test',
    'pin tokenizer, weights and config as one version, key caches by version, keep a session on one version during a canary'
]

print(f"\n4. Checking fidelity for {len(expected_source_labels)} expected source labels:")
for exp in expected_source_labels:
    assert exp in texts, f"Missing expected label:\n  '{exp}'"
    print(f"   [PASS] '{exp[:50]}...'")

assert len(texts) == len(expected_source_labels), f"Expected {len(expected_source_labels)} text elements, got {len(texts)}"
print("\n[ALL CHECKS PASSED] Perfect 1-to-1 match!")
