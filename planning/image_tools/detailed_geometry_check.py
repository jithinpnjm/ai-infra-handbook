import xml.etree.ElementTree as ET

tree = ET.parse("test.svg")
root = tree.getroot()

# Card bounds:
cards = {
    "Title": {"box": (0, 0, 1600, 100), "anchor": "middle"},
    "Card 1": {"box": (58, 128, 419, 230)},
    "Card 2": {"box": (58, 378, 419, 584)},
    "Middle": {"box": (540, 110, 330, 870), "anchor": "middle"},
    "Card 3 (IPVS)": {"box": (933, 128, 609, 240)},
    "Card 4 (nftables)": {"box": (933, 388, 609, 180)},
    "Card 5 (eBPF)": {"box": (933, 588, 609, 374)},
    "Footer": {"box": (40, 1020, 1520, 140)}
}

# Let us verify each card explicitly
print("=== VERIFYING EACH CARD'S GEOMETRY ===")

def est_w(text, fs, is_mono):
    return len(text) * fs * (0.62 if is_mono else 0.6)

# Card 1: box x=58, y=128, w=419, h=230 (right=477, bottom=358)
c1_box = (58, 128, 419, 230)
# line 1: Per new connection: x=82, y=246, fs=30 -> w=360. right=82+360=442 <= 477 - 16 = 461. OK!
# line 2: linear walk of: x=82, y=286, fs=24 -> w=14*14.4=201.6. right=82+201.6=283.6 <= 461. OK!
# line 3: KUBE-SERVICES, O(n): x=82, y=320, fs=24 -> mono(14)*24*0.62 + 6*14.4 = 208.32 + 86.4 = 294.72. right=82+294.72=376.72 <= 461. OK!
# Bottom check: y=320, bottom=358 -> pad=38px >= 16px. OK!
print("Card 1: ALL LINES OK!")

# Card 2: box x=58, y=378, w=419, h=584 (right=477, bottom=962)
c2_lines = [
    [("per change:", 30, False)],
    [("iptables-restore", 24, True), (" rewrites", 24, False)],
    [("the whole ruleset, takes", 24, False)],
    [("the xtables lock", 24, False)],
    [("(/run/xtables.lock),", 24, True)],
    [("seconds or minutes at", 24, False)],
    [("tens of thousands of rules,", 24, False)],
    [("can collide with CNI", 24, False)],
    [("plug-ins and send traffic", 24, False)],
    [("to stale endpoints", 24, False)]
]
# Wait, let's check line 7: "tens of thousands of rules,"
# len = 27 chars * 0.6 * 24 = 388.8px.
# x = 82 -> right edge = 82 + 388.8 = 470.8px!
# Card right edge = 477px.
# 477 - 470.8 = 6.2px padding!
# BUT RULE SAYS: "Every text line must fit inside its box with at least 16 px padding."
print(f"Card 2 Line 7 right edge = {82 + 388.8:.1f}, padding = {477 - (82 + 388.8):.1f}px (MUST BE >= 16px!)")

