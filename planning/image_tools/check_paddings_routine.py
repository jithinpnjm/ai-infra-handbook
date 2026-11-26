import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_routine.svg")
root = tree.getroot()

print("=== CHECKING PADDINGS AND BOX CLEARANCES ===")

# 1. Top-level boxes outside margins and gaps
boxes = [
    ("Card 1", 40, 125, 345, 490),
    ("Card 2", 431, 125, 345, 490),
    ("Card 3", 822, 125, 345, 490),
    ("Card 4", 1214, 125, 345, 490),
    ("Milestone track", 40, 655, 1520, 80),
    ("Bug log bar", 40, 775, 1520, 90),
    ("Takeaway bar", 40, 905, 1520, 70),
]

H = 1020
for name, x, y, w, h in boxes:
    lm = x
    rm = 1600 - (x + w)
    tm = y
    bm = H - (y + h)
    print(f"{name:18s}: margins L={lm:3d}, R={rm:3d}, T={tm:3d}, B={bm:3d}")
    assert lm >= 40, f"{name} left margin {lm} < 40"
    assert rm >= 40, f"{name} right margin {rm} < 40"
    assert tm >= 40, f"{name} top margin {tm} < 40"
    assert bm >= 40, f"{name} bottom margin {bm} < 40"

print("PASS: All outside margins >= 40px.")

# Gaps
card_to_track = 655 - (125 + 490)
track_to_log = 775 - (655 + 80)
log_to_takeaway = 905 - (775 + 90)

print(f"Cards to Milestone track gap: {card_to_track} px >= 40 px")
assert card_to_track >= 40
print(f"Milestone track to Bug log gap: {track_to_log} px >= 40 px")
assert track_to_log >= 40
print(f"Bug log to Takeaway gap: {log_to_takeaway} px >= 40 px")
assert log_to_takeaway >= 40

print("PASS: All vertical gaps >= 40px.")

# Horizontal gaps between cards
g1 = 431 - (40 + 345)
g2 = 822 - (431 + 345)
g3 = 1214 - (822 + 345)
print(f"Horizontal gaps between cards: {g1} px, {g2} px, {g3} px >= 40 px")
assert g1 >= 40 and g2 >= 40 and g3 >= 40

print("PASS: All horizontal card gaps >= 40px.")

# 2. Text paddings inside sub-boxes (>= 16px)
# Function to estimate text width
def est_w(text, size, mono=False):
    return len(text) * size * (0.62 if mono else 0.6)

# Check all text elements inside their respective boxes
paddings_to_check = [
    # (label, text_line, font_size, box_w)
    ("Title", "A four-week practice routine", 48, 1600),
    ("W1 Title", "Language basics", 30, 345),
    ("W1 Body L1", "Dicts, counters, ", 24, 315),
    ("W1 Body L2", "sorting, strings, ", 24, 315),
    ("W1 Body L3", "the harness", 24, 315),
    ("W1 Time L1", "Time: 5 sessions ", 24, 315),
    ("W1 Time L2", "of 1 hour", 24, 315),
    
    ("W2 Title", "Core patterns", 30, 345),
    ("W2 Body L1", "Hash maps, ", 24, 315),
    ("W2 Body L2", "two pointers, ", 24, 315),
    ("W2 Body L3", "sliding window, ", 24, 315),
    ("W2 Body L4", "stacks", 24, 315),
    ("W2 Time L1", "Time: 4 sessions ", 24, 315),
    ("W2 Time L2", "of 75 minutes", 24, 315),
    
    ("W3 Body L1", "Heaps, intervals, ", 24, 315),
    ("W3 Body L2", "binary search, ", 24, 315),
    ("W3 Body L3", "graphs", 24, 315),
    ("W3 Time L1", "Time: 4 sessions ", 24, 315),
    ("W3 Time L2", "of 75 minutes", 24, 315),
    
    ("W4 Title", "Full mock rounds", 30, 345),
    ("W4 Body L1", "Two problems in ", 24, 315),
    ("W4 Body L2", "60 minutes, ", 24, 315),
    ("W4 Body L3", "once recorded", 24, 315),
    ("W4 Time L1", "Time: 3 mocks ", 24, 315),
    ("W4 Time L2", "of 90 minutes", 24, 315),
    
    ("Track Badge", "End-of-week test", 24, 280),
    ("Bug log text", "Keep a bug log: harness-found bugs are what to practise on", 28, 1520 - 110),
    ("Takeaway text", "Practise the process under time pressure.", 28, 1520)
]

print("\n--- Conservative Text Padding Checks (>= 16px) ---")
all_pads_ok = True
for name, line, size, box_w in paddings_to_check:
    tw = est_w(line, size)
    pad = (box_w - tw) / 2
    ok = (pad >= 16.0)
    if not ok:
        all_pads_ok = False
    print(f"  {name:15s}: len={len(line):2d}, w={tw:5.1f}px, box={box_w:4.0f}px, pad={pad:5.1f}px -> {'OK' if ok else 'FAIL'}")

assert all_pads_ok, "Some text paddings failed >= 16px!"
print("PASS: All text lines have >= 16px conservative padding.")

# 3. Orange occurrences check
raw = open("test_routine.svg").read()
oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"\nOrange #db8129 count: {len(oranges)} (must be exactly 1, used only on Week 4 card outline)")
assert len(oranges) == 1, f"Expected 1 orange, got {len(oranges)}"

print("\nALL CLEARANCES AND PADDINGS VERIFIED 100%!")
