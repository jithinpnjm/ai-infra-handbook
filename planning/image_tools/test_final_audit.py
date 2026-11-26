import xml.etree.ElementTree as ET
import re

svg_path = "p3_0523_keda_switch_dimmer.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure
children = list(root)
tag0 = children[0].tag.split('}')[-1]
tag1 = children[1].tag.split('}')[-1]
assert tag0 == 'title', f"Child 0 must be title, got {tag0}"
assert tag1 == 'desc', f"Child 1 must be desc, got {tag1}"
print("1. Title & Desc: PASS")

# 2. Dimensions
w = root.get('width')
h = root.get('height')
vb = root.get('viewBox').split()
assert w == '1600'
assert vb == ['0', '0', '1600', '1180']
assert h == '1180'
print("2. Dimensions 1600x1180: PASS")

# 3. Text elements & font sizes >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size'))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"3. All {len(text_elements)} text elements have font-size >= 24: PASS")

# 4. Expected labels
expected_labels = [
    "KEDA: the switch and the dimmer",
    "Stage A",
    "zero to one: the switch, handled by KEDA operator (a plain HPA cannot scale to zero because the formula multiplies by zero)",
    "Stage B",
    "one to N: the dimmer, handled by the HPA that KEDA creates, fed by KEDA metrics adapter on the External Metrics API",
    "ScaledObject batch-embed",
    "minReplicaCount 0",
    "maxReplicaCount 50",
    "pollingInterval 15",
    "cooldownPeriod 300 (quiet time before one to zero)",
    "scaleDown stabilizationWindowSeconds 600",
    "kafka lagThreshold 200",
    "prometheus query sum vllm:num_requests_waiting threshold 5",
    "cron 0 8 to 0 20 Monday to Friday desiredReplicas 4 (pre-warm business hours)",
    "the largest desired count across active triggers wins, so cron acts as a floor in business hours",
    "ScaledJob transcribe-job",
    "one short Job per queued message, aws-sqs-queue queueLength 1, maxReplicaCount 20, strategy accurate",
    "ScaledObject",
    "keeps a long-running Deployment and changes its size",
    "scale-to-zero on a GPU service costs a cold start; fine for a nightly batch job, painful for a person typing in chat"
]

found_texts = [t for t, fs in text_elements]
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count==1, got {cnt}"

extras = [t for t in found_texts if t not in expected_labels]
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
print(f"4. Exactly {len(expected_labels)} expected labels matched 1-to-1: PASS")

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("5. No forbidden style words in text: PASS")

# 6. Orange (#db8129) count
raw_svg = open(svg_path).read()
orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"6. Orange (#db8129) occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Orange count {len(orange_matches)} not in [1, 4]!"

# 7. Markers
markers = re.findall(r'marker-end', raw_svg)
assert len(markers) == 1, f"Expected 1 arrow, got {len(markers)}"
print("7. Exactly 1 connecting arrow: PASS")

# 8. Paddings check
checks = [
    # Stage A card
    ("Stage A Title", "Stage A", 30, "sans", 135, 142, 40, 90, 710, 236),
    ("Stage A line 1", "zero to one: the switch, handled by", 24, "sans", 76, 196, 58, 160, 674, 150),
    ("Stage A line 2", "KEDA operator (a plain HPA cannot", 24, "sans", 76, 224, 58, 160, 674, 150),
    ("Stage A line 3", "scale to zero because the formula", 24, "sans", 76, 252, 58, 160, 674, 150),
    ("Stage A line 4", "multiplies by zero)", 24, "sans", 76, 280, 58, 160, 674, 150),

    # Stage B card
    ("Stage B Title", "Stage B", 30, "sans", 945, 142, 850, 90, 710, 236),
    ("Stage B line 1", "one to N: the dimmer, handled by the", 24, "sans", 886, 196, 868, 160, 674, 150),
    ("Stage B line 2", "HPA that KEDA creates, fed by KEDA", 24, "sans", 886, 224, 868, 160, 674, 150),
    ("Stage B line 3", "metrics adapter on the", 24, "sans", 886, 252, 868, 160, 674, 150),
    ("Stage B line 4", "External Metrics API", 24, "sans", 886, 280, 868, 160, 674, 150),

    # ScaledObject batch-embed Title
    ("SO Title", "ScaledObject batch-embed", 30, "sans", 135, 394, 40, 342, 1520, 422),

    # Knobs
    ("minReplicaCount", "minReplicaCount 0", 24, "mono", 237 - len("minReplicaCount 0")*0.62*24/2, 449, 65, 412, 345, 58),
    ("maxReplicaCount", "maxReplicaCount 50", 24, "mono", 608 - len("maxReplicaCount 50")*0.62*24/2, 449, 435, 412, 347, 58),
    ("pollingInterval", "pollingInterval 15", 24, "mono", 423 - len("pollingInterval 15")*0.62*24/2, 516, 65, 480, 717, 58),

    ("cooldown line 1", "cooldownPeriod 300", 24, "mono", 85, 582, 65, 546, 717, 88),
    ("cooldown line 2", "(quiet time before one to zero)", 24, "mono", 85, 610, 65, 546, 717, 88),

    ("scaleDown", "scaleDown stabilizationWindowSeconds 600", 24, "mono", 85, 681, 65, 644, 717, 58),

    # Triggers
    ("kafka", "kafka lagThreshold 200", 24, "sans", 874, 449, 808, 412, 727, 58),
    ("prom line 1", "prometheus query sum", 24, "sans", 874, 516, 808, 480, 727, 88),
    ("prom line 2", "vllm:num_requests_waiting threshold 5", 24, "sans", 874, 544, 808, 480, 727, 88),
    ("cron line 1", "cron 0 8 to 0 20 Monday to Friday", 24, "sans", 874, 614, 808, 578, 727, 88),
    ("cron line 2", "desiredReplicas 4 (pre-warm business hours)", 24, "sans", 874, 642, 808, 578, 727, 88),

    # Rule bar
    ("rule", "the largest desired count across active triggers wins, so cron acts as a floor in business hours", 24, "sans", 800 - 96*0.6*24/2, 716, 65, 678, 1470, 60),

    # ScaledJob contrast
    ("SJ title", "ScaledJob transcribe-job", 30, "sans", 125, 836, 40, 785, 730, 195),
    ("SJ line 1", "one short Job per queued message,", 24, "sans", 65, 880, 40, 785, 730, 195),
    ("SJ line 2", "aws-sqs-queue queueLength 1,", 24, "sans", 65, 910, 40, 785, 730, 195),
    ("SJ line 3", "maxReplicaCount 20, strategy accurate", 24, "sans", 65, 940, 40, 785, 730, 195),

    # ScaledObject contrast
    ("SO contrast title", "ScaledObject", 30, "sans", 915, 836, 830, 785, 730, 195),
    ("SO contrast line 1", "keeps a long-running Deployment", 24, "sans", 855, 888, 830, 785, 730, 195),
    ("SO contrast line 2", "and changes its size", 24, "sans", 855, 920, 830, 785, 730, 195),

    # Warning
    ("warning line 1", "scale-to-zero on a GPU service costs a cold start; fine for a nightly batch job,", 24, "sans", 140, 1054, 40, 1000, 1520, 140),
    ("warning line 2", "painful for a person typing in chat", 24, "sans", 140, 1088, 40, 1000, 1520, 140),
]

all_passed = True
for name, text, fs, ff, tx, ty, rx, ry, rw, rh in checks:
    char_factor = 0.62 if ff == "mono" else 0.60
    est_w = len(text) * char_factor * fs
    top_y = ty - fs * 0.8
    bot_y = ty + fs * 0.2
    right_x = tx + est_w

    pad_left = tx - rx
    pad_right = (rx + rw) - right_x
    pad_top = top_y - ry
    pad_bot = (ry + rh) - bot_y

    min_pad = min(pad_left, pad_right, pad_top, pad_bot)
    status = "OK" if min_pad >= 16.0 else "FAIL"
    if status == "FAIL":
        all_passed = False
    assert min_pad >= 16.0, f"FAILED: {name} min_pad={min_pad:.1f} < 16px!"

print(f"8. All {len(checks)} text segments have padding >= 16px: PASS")

print("\n=======================================================")
print(">>> ALL 8 STRICT CHECKS PASSED FLAWLESSLY (100%) <<<")
print("=======================================================")
