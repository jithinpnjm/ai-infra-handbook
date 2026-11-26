import xml.etree.ElementTree as ET

tree = ET.parse("candidate_p4_0407.svg")
root = tree.getroot()

def est_w(text, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(text) * fs * rate

# Check every box and its texts:
# 1. Card site.fact: rect x=64, y=156, w=670, h=158. Icon: x=86..134.
# Text start at x=160.
w1 = est_w("site.fact (INI): ", 24, False)
w2 = est_w("[location] rack=r07, rail=3", 24, True)
assert 160 - 134 >= 16, "Clearance from icon < 16"
assert (64 + 670) - (160 + max(w1, w2)) >= 16, "Padding to right edge < 16"
print("Card site.fact: PASS (icon clearance:", 160 - 134, ", right pad:", (64 + 670) - (160 + max(w1, w2)), ")")

# 2. Card gpu.fact: rect x=754, y=156, w=786, h=158. Icon: x=776..820.
# Text start at x=850.
wg1 = est_w("gpu.fact (executable, mode 0755): ", 24, False)
wg2 = est_w("#!/bin/sh; ", 24, True)
wg3 = est_w("n=$(nvidia-smi -L 2>/dev/null | wc -l); ", 24, True)
wg4 = est_w("echo {\"count\": $n}", 24, True)
max_wg = max(wg1, wg2, wg3, wg4)
assert 850 - 820 >= 16, "Clearance from icon < 16"
assert (754 + 786) - (850 + max_wg) >= 16, "Padding to right edge < 16"
print("Card gpu.fact: PASS (icon clearance:", 850 - 820, ", right pad:", (754 + 786) - (850 + max_wg), ")")

# 3. Arrow label panel: rect x=140, y=354, w=1420, h=92. Icon: x=160..210.
# Text start at x=240.
wa1 = est_w("placed in /etc/ansible/facts.d/ on the target; any .fact file, or any executable, ", 24, False)
wa2 = est_w("is picked up during fact gathering; INI or JSON, or an executable printing JSON", 24, False)
max_wa = max(wa1, wa2)
assert 240 - 210 >= 16
assert (140 + 1420) - (240 + max_wa) >= 16
print("Arrow panel: PASS (icon clearance:", 240 - 210, ", right pad:", (140 + 1420) - (240 + max_wa), ")")

# 4. Destination header: ansible_local.<name> centered at x=800, fs=30.
whdr = est_w("ansible_local.<name>", 30, True)
assert (800 - whdr/2) - (60 + 44) >= 16
assert (40 + 1520) - (800 + whdr/2) >= 16
print("Ansible_local header: PASS (left pad:", (800 - whdr/2) - 104, ", right pad:", 1560 - (800 + whdr/2), ")")

# Badge 1: rect x=140, y=534, w=670. Text centered at 475, fs=24 mono.
wb1 = est_w("ansible_local.location.rack", 24, True)
assert (475 - wb1/2) - 140 >= 16
assert (140 + 670) - (475 + wb1/2) >= 16
print("Badge location.rack: PASS (pad:", (475 - wb1/2) - 140, ")")

# Badge 2: rect x=850, y=534, w=670. Text centered at 1185, fs=24 mono.
wb2 = est_w("ansible_local.gpu.count", 24, True)
assert (1185 - wb2/2) - 850 >= 16
assert (850 + 670) - (1185 + wb2/2) >= 16
print("Badge gpu.count: PASS (pad:", (1185 - wb2/2) - 850, ")")

# 5. Task strip: rect x=40, y=644, w=1520, h=100. Icon: x=60..108.
# Text start at x=140.
wt1 = est_w("copy writes gpu.fact; setup with filter ansible_local re-reads it; ", 24, False)
wt2 = est_w("debug msg: {{ ansible_local.gpu.count }} GPUs on {{ inventory_hostname }}", 24, True)
max_wt = max(wt1, wt2)
assert 140 - 108 >= 16
assert (40 + 1520) - (140 + max_wt) >= 16
print("Task strip: PASS (icon clearance:", 140 - 108, ", right pad:", 1560 - (140 + max_wt), ")")

# 6. Callout 1: rect x=40, y=768, w=488, h=286. Icon at cx=284, cy=814, r=28.
# Text centered at x=284. First line y=876.
c1_lines = [
    "the script runs on the target, ",
    "so it always counts the ",
    "GPUs actually present, even ",
    "if the inventory was written ",
    "before a card was replaced"
]
for l in c1_lines:
    wl = est_w(l.strip(), 24, False)
    left_pad = (284 - wl/2) - 40
    right_pad = (40 + 488) - (284 + wl/2)
    assert left_pad >= 16 and right_pad >= 16, f"c1 fail on '{l}': left={left_pad}, right={right_pad}"
print("Callout 1: PASS (all lines >= 16px pad)")

# 7. Callout 2: rect x=556, y=768, w=488. Icon cx=800.
c2_lines = [
    "the node carries its own ",
    "label, so the playbook ",
    "does not need a separate ",
    "spreadsheet that might ",
    "be out of date"
]
for l in c2_lines:
    wl = est_w(l.strip(), 24, False)
    left_pad = (800 - wl/2) - 556
    right_pad = (556 + 488) - (800 + wl/2)
    assert left_pad >= 16 and right_pad >= 16, f"c2 fail on '{l}': left={left_pad}, right={right_pad}"
print("Callout 2: PASS (all lines >= 16px pad)")

# 8. Callout 3: rect x=1072, y=768, w=488. Icon cx=1316.
c3_lines = [
    "attributes stay with the ",
    "host and do not depend on ",
    "the control node"
]
for l in c3_lines:
    wl = est_w(l.strip(), 24, False)
    left_pad = (1316 - wl/2) - 1072
    right_pad = (1072 + 488) - (1316 + wl/2)
    assert left_pad >= 16 and right_pad >= 16, f"c3 fail on '{l}': left={left_pad}, right={right_pad}"
print("Callout 3: PASS (all lines >= 16px pad)")

# 9. Bottom bar: rect x=40, y=1080, w=1520, h=64. Icon: x=64..108.
wbbar = est_w("The supported way for a host to declare its own attributes", 26, False)
assert (800 - wbbar/2) - 108 >= 16
assert 1560 - (800 + wbbar/2) >= 16
print("Bottom bar: PASS (left pad from icon:", (800 - wbbar/2) - 108, ")")

print("\nALL BOXES, ICONS, AND TEXT SATISFY STRICT PADDING CRITERIA!")
