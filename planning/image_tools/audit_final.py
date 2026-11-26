import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_adapter_pipeline.svg")
root = tree.getroot()

# 1. First children
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"1. First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"

# 2. Dimensions
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"2. Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600"
assert h == "1200"
assert vb == "0 0 1600 1200"

# 3. Font sizes >= 24px
font_sizes = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = int(el.attrib.get('font-size', '0'))
    tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        for ts in tspans:
            t_content = (ts.text or "").strip()
            t_fs = int(ts.attrib.get('font-size', fs))
            font_sizes.append((t_content, t_fs))
    else:
        t_content = "".join(el.itertext()).strip()
        font_sizes.append((t_content, fs))

print(f"3. All text segments count: {len(font_sizes)}")
for t, fs in font_sizes:
    assert fs >= 24, f"Text '{t}' has font-size {fs} < 24 px!"
print("   [PASS] All font sizes >= 24 px.")

# 4. Source labels
source_labels = [
    "From a vLLM metric to an HPA decision",
    "vLLM pod exposes vllm:num_requests_waiting",
    "Prometheus scrapes it",
    "prometheus-adapter rule: seriesQuery vllm:num_requests_waiting with namespace and pod labels; resources overrides map namespace and pod; name as vllm_requests_waiting; metricsQuery sum by group",
    "custom.metrics.k8s.io API",
    "HPA reads it and decides",
    "kafka_consumergroup_lag topic embed",
    "rule name kafka_lag",
    "external.metrics.k8s.io",
    "kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/serving/pods/*/vllm_requests_waiting",
    "kubectl get --raw /apis/external.metrics.k8s.io/v1beta1/namespaces/serving/kafka_lag",
    "kubectl describe hpa vllm -n serving",
    "AbleToScale: can the HPA change the count at all",
    "ScalingActive: can it read the metrics",
    "ScalingLimited: has a minimum or maximum capped the result",
    "if the first command returns nothing, no amount of tuning helps"
]

full_texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    txt = " ".join("".join(el.itertext()).split())
    if txt.isdigit():
        continue
    full_texts.append(txt)

print(f"\n4. Checking {len(source_labels)} source labels:")
for sl in source_labels:
    cnt = full_texts.count(sl)
    if cnt != 1:
        print(f"   [FAIL] Label '{sl}': count={cnt}")
    else:
        print(f"   [OK] Label '{sl}'")
    assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}"

assert len(full_texts) == len(source_labels), f"Expected {len(source_labels)} text labels, got {len(full_texts)}: {set(full_texts) - set(source_labels)}"
print("   [PASS] Every source label appears exactly once, and no extra text exists.")

# 5. Banned words
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for bw in banned_words:
        assert bw not in words, f"Banned styling word '{bw}' found in text: '{ft}'"
print("   [PASS] No styling words printed as text.")

# 6. Arrows count
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"\n6. Arrow count: {len(arrows)}")
assert len(arrows) == 6, f"Expected 6 arrows, got {len(arrows)}"
print("   [PASS] Exactly 6 arrows present.")

# 7. Orange highlight
svg_str = open("candidate_adapter_pipeline.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange highlights: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Expected exactly 1 orange element, got {len(orange_matches)}"
print("   [PASS] Exactly one orange highlight used.")

# 8. External resources
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"
print("   [PASS] No external images, scripts or fonts.")

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
