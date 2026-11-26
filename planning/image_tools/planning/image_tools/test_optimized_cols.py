#!/usr/bin/env python3

# Optimize column widths to guarantee >= 16px padding everywhere!
# Total width available: 1520 px (from x = 40 to 1560)
# Gaps between columns: 12 px * 3 = 36 px.
# Available for 4 columns: 1520 - 36 = 1484 px.

# Col 1: Type. Longest: ContainerResource (244.8 px). Width = 285. Min pad = (285 - 244.8)/2 = 20.1 px >= 16!
# Col 2: Source API. Longest: external.metrics.k8s.io (342.2 px). Width = 380. Min pad = (380 - 342.2)/2 = 18.9 px >= 16!
# Col 3: Provider. Longest: Adapter or cloud adapters (360.0 px). Text at x_left + 18. Width = 398. Right pad = 398 - (18 + 360) = 20 px >= 16!
# Col 4: Example. Longest: requests, or average value (374.4 px). Text at x_left + 20. Width = 421. Right pad = 421 - (20 + 374.4) = 26.6 px >= 16!

# Sum of widths: 285 + 380 + 398 + 421 = 1484 px!
# Perfect match!

c1_w = 285
c2_w = 380
c3_w = 398
c4_w = 421

gap = 12
x0 = 40

c1_x = x0
c2_x = c1_x + c1_w + gap
c3_x = c2_x + c2_w + gap
c4_x = c3_x + c3_w + gap

print(f"Col 1: x={c1_x}, w={c1_w}, x_end={c1_x + c1_w}")
print(f"Col 2: x={c2_x}, w={c2_w}, x_end={c2_x + c2_w}")
print(f"Col 3: x={c3_x}, w={c3_w}, x_end={c3_x + c3_w}")
print(f"Col 4: x={c4_x}, w={c4_w}, x_end={c4_x + c4_w}")
assert c4_x + c4_w == 1560

# Check every item:
items = [
    # Col 1 (centered):
    ("ContainerResource", 285, 24, False, True),
    ("Resource", 285, 28, False, True),
    ("Pods", 285, 28, False, True),
    ("Object", 285, 28, False, True),
    ("External", 285, 28, False, True),

    # Col 2 (centered):
    ("external.metrics.k8s.io", 380, 24, True, True),
    ("custom.metrics.k8s.io", 380, 24, True, True),
    ("metrics.k8s.io", 380, 25, True, True),
    ("for one object", 380, 24, False, True),
    ("per container", 380, 24, False, True),

    # Col 3 (left aligned at pad_l=18):
    ("Adapter or cloud adapters", 398, 24, False, False),
    ("via Prometheus Adapter,", 398, 24, False, False),
    ("KEDA or vendor adapters", 398, 24, False, False),
    ("metrics-server from", 398, 24, False, False),
    ("kubelet and cAdvisor", 398, 24, False, False),
    ("via KEDA, Prometheus", 398, 24, False, False),

    # Col 4 (left aligned at pad_l=20):
    ("requests, or average value", 421, 24, False, False),
    ("scale on the app container", 421, 24, False, False),
    ("utilisation relative to", 421, 24, False, False),
    ("per-pod requests_in_flight", 421, 24, False, False),
    ("SQS queue length, Pub/Sub", 421, 24, False, False),
    ("Ingress", 421, 24, False, False),
    ("requests_per_second", 421, 24, False, False),
]

all_ok = True
for text, box_w, fs, is_mono, is_centered in items:
    factor = 0.62 if is_mono else 0.60
    w = len(text) * factor * fs
    if is_centered:
        pad_l = (box_w - w) / 2
        pad_r = pad_l
    else:
        pad_l = 18 if box_w == 398 else 20
        pad_r = box_w - (pad_l + w)
    min_pad = min(pad_l, pad_r)
    status = "OK" if min_pad >= 16.0 else "FAIL"
    if min_pad < 16.0:
        all_ok = False
    print(f"[{status}] '{text}': w={w:.1f}, pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, min_pad={min_pad:.1f}")

assert all_ok
print("\nPERFECT! EVERY SINGLE TEXT LINE HAS >= 16 PX PADDING ON ALL SIDES!")
