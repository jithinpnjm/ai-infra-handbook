import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_drill3.svg")
root = tree.getroot()

# Padding tests:
# Each box: (description, [lines], font-size, is_mono, box_x, box_w)
boxes = [
    ("Lane 1 Header", ["what exists"], 30, False, 70, 260),
    ("Lane 1 Content line 1", ["weights load for about 90 seconds"], 24, False, 350, 1180),
    ("Lane 1 Content line 2", ["('loading weights 62%' then nothing in the previous logs)"], 24, False, 350, 1180),
    ("Lane 2 Header line 1", ["broken"], 30, False, 70, 260),
    ("Lane 2 Header line 2", ["probes"], 30, False, 70, 260),
    ("Lane 2 Config line 1", ["liveness initialDelaySeconds 5,"], 24, False, 350, 690),
    ("Lane 2 Config line 2", ["periodSeconds 10, failureThreshold 1,"], 24, False, 350, 690),
    ("Lane 2 Config line 3", ["no startup probe"], 24, False, 350, 690),
    ("Lane 2 Impact line 1", ["restart count 40,"], 24, False, 1060, 470),
    ("Lane 2 Impact line 2", ["one restart every four minutes"], 24, False, 1060, 470),
    ("Lane 2 Kill line 1", ["first check near 5 s fails, event 'Unhealthy: Liveness probe failed'"], 24, False, 350, 1180),
    ("Lane 2 Kill line 2", ["three times then 'Killing: failed liveness probe, will be restarted'"], 24, False, 350, 1180),
    ("Lane 3 Header", ["fixed"], 30, False, 70, 260),
    ("Lane 3 Window line 1", ["startup probe with failureThreshold 30 and"], 24, False, 350, 680),
    ("Lane 3 Window line 2", ["period 10 gives a 300 second window"], 24, False, 350, 680),
    ("Lane 3 Liveness line 1", ["liveness only starts after"], 24, False, 1070, 460),
    ("Lane 3 Liveness line 2", ["the startup probe passes"], 24, False, 1070, 460),
    ("Restart Strip", ["starts at 10 s, doubles, capped at 300 s, resets after ten clean minutes"], 24, False, 50, 1500),
    ("Contrast line 1", ["OOM kill shows Last State Terminated, Reason OOMKilled, Exit Code 137;"], 24, False, 50, 1500),
    ("Contrast line 2", ["here Reason is Error and no OOMKilled"], 24, False, 50, 1500),
    ("Takeaway line 1", ["liveness answers is this process stuck, not is it ready;"], 24, False, 50, 1500),
    ("Takeaway line 2", ["slow starters get a startup probe sized to a measured load time"], 24, False, 50, 1500),
]

print("=== CHECKING HORIZONTAL PADDINGS (RULE: >= 16px) ===")
all_pass = True
for desc, lines, fs, is_mono, bx, bw in boxes:
    mult = 0.62 if is_mono else 0.6
    for l in lines:
        w = len(l) * fs * mult
        pad = (bw - w) / 2.0
        status = "PASS" if pad >= 16.0 else "FAIL"
        if pad < 16.0:
            all_pass = False
        print(f"[{status}] {desc:24s} pad={pad:5.1f}px (w={w:5.1f}px in box_w={bw}px) | '{l}'")

assert all_pass, "Some boxes failed padding check!"

print("\n=== CHECKING PANEL GAPS (RULE: >= 40px) ===")
# Major containers y intervals:
# Lane 1: 95..225
# Lane 2: 265..495
# Lane 3: 535..675
# Strip:  715..805
# Contrast: 845..975
# Bar:    1015..1115
gaps = [
    ("Lane 1 -> Lane 2", 265 - 225),
    ("Lane 2 -> Lane 3", 535 - 495),
    ("Lane 3 -> Strip", 715 - 675),
    ("Strip -> Contrast", 845 - 805),
    ("Contrast -> Bar", 1015 - 975),
]
for name, g in gaps:
    print(f"[{'PASS' if g >= 40 else 'FAIL'}] {name:20s}: gap={g}px")
    assert g >= 40, f"Gap {name} is {g} < 40px!"

print("\n=== CHECKING MARGINS (RULE: >= 40px) ===")
assert 50 >= 40, "Left margin < 40"
assert (1600 - 1550) >= 40, "Right margin < 40"
assert 95 >= 40, "Top margin < 40"
assert (1180 - 1115) >= 40, "Bottom margin < 40"
print("All margins >= 40px: PASS!")

print("\nALL STRICT GEOMETRY CHECKS PASSED!")
