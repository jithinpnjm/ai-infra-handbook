# Check all boxes, gaps, and margins
boxes = {
    "start": (680, 75, 560, 75),
    "step1": (680, 195, 560, 75),
    "step2": (680, 315, 560, 75),
    "suspect": (40, 525, 320, 225),
    "badge_b": (430, 435, 320, 115),
    "repeat": (410, 590, 340, 150),
    "memory": (790, 600, 210, 135),
    "drain": (450, 790, 260, 110),
    "badge_a": (1040, 485, 210, 115),
    "ignore": (1040, 790, 210, 110),
    "badge_c": (1300, 465, 260, 175),
    "drain_at_once": (1290, 790, 270, 110),
    "takeaway": (40, 940, 1520, 100),
}

# Outside margins
for k, (x, y, w, h) in boxes.items():
    lm = x
    rm = 1600 - (x + w)
    tm = y
    bm = 1080 - (y + h)
    assert lm >= 40, f"{k} left {lm} < 40"
    assert rm >= 40, f"{k} right {rm} < 40"
    assert tm >= 40, f"{k} top {tm} < 40"
    assert bm >= 40, f"{k} bot {bm} < 40"

# Gaps
assert boxes["step1"][1] - (boxes["start"][1] + boxes["start"][3]) >= 40
assert boxes["step2"][1] - (boxes["step1"][1] + boxes["step1"][3]) >= 40
assert boxes["repeat"][0] - (boxes["suspect"][0] + boxes["suspect"][2]) >= 40
assert boxes["memory"][0] - (boxes["repeat"][0] + boxes["repeat"][2]) >= 40
assert boxes["ignore"][0] - (boxes["memory"][0] + boxes["memory"][2]) >= 40
assert boxes["drain_at_once"][0] - (boxes["ignore"][0] + boxes["ignore"][2]) >= 40
assert boxes["drain"][1] - (boxes["repeat"][1] + boxes["repeat"][3]) >= 40
assert boxes["takeaway"][1] - (boxes["drain"][1] + boxes["drain"][3]) >= 40

print("MASTER GEOMETRY AUDIT PASSED 100%!")
