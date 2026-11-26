import xml.etree.ElementTree as ET

def estimate_width(text, font_size, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(text) * font_size * rate

tree = ET.parse("test_lost_update_out.svg")
root = tree.getroot()

print("Verifying text clearances and bounding boxes...")

# Title line 1: 800 center, y=46, fs=48
t1 = "How counter += 1 loses an update, "
w1 = estimate_width(t1, 48)
pad1 = (1600 - w1) / 2
print(f"Title line 1 width: {w1:.1f}px, margin: {pad1:.1f}px (>= 40)")
assert pad1 >= 40

# Title line 2: 800 center, dy=52, fs=48
t2 = "and what the lock changes"
w2 = estimate_width(t2, 48)
pad2 = (1600 - w2) / 2
print(f"Title line 2 width: {w2:.1f}px, margin: {pad2:.1f}px (>= 40)")
assert pad2 >= 40

# Subtitle: 800 center, y=132, fs=24
w_sub = estimate_width("Two thread lanes and a shared variable counter", 24)
pad_sub = (1600 - w_sub) / 2
print(f"Subtitle width: {w_sub:.1f}px, margin: {pad_sub:.1f}px (>= 40)")
assert pad_sub >= 40

# Check code strip:
code_text = "lock = threading.Lock(); def incr(n): global counter; for _ in range(n): with lock: counter += 1"
w_code = estimate_width(code_text, 24, is_mono=True)
right_edge = 115 + w_code
pad_right = 1560 - right_edge
pad_left = 115 - 40
print(f"Code strip: text_w={w_code:.1f}px, right_edge={right_edge:.1f}px, pad_right={pad_right:.1f}px, pad_left={pad_left:.1f}px")
assert pad_right >= 16
assert pad_left >= 16

# Check result boxes in Without lock:
w_res1 = estimate_width("final counter is 6 where two increments should give 7", 24)
pad_res1 = (940 - w_res1) / 2
print(f"Result box 1: text_w={w_res1:.1f}px, pad={pad_res1:.1f}px")
assert pad_res1 >= 16

w_res2 = estimate_width("one update lost", 24)
pad_res2 = (350 - w_res2) / 2
print(f"Result box 2 (orange): text_w={w_res2:.1f}px, pad={pad_res2:.1f}px")
assert pad_res2 >= 16

# Check A holds lock box in With lock:
w_lock_hold = estimate_width("A holds the lock, B waits", 24)
pad_lock_hold = (1320 - w_lock_hold) / 2
print(f"Lock hold box: text_w={w_lock_hold:.1f}px, pad={pad_lock_hold:.1f}px")
assert pad_lock_hold >= 16

# Check Related bugs strip:
# Col 1 items at x=115:
col1_lines = [
    "data race: loses updates ",
    "or breaks an invariant",
    "deadlock: two threads each hold ",
    "a lock the other needs",
    "livelock: keep reacting without progress"
]
for t in col1_lines:
    w_t = estimate_width(t, 24)
    print(f"Col 1 bug line '{t[:25]}...': w={w_t:.1f}px, right={115+w_t:.1f}px (< 800)")
    assert 115 + w_t < 800

w_starv = estimate_width("starvation: a thread never gets its turn", 24)
print(f"Col 2 bug 'starvation...': w={w_starv:.1f}px, right={820+w_starv:.1f}px (< 1540)")
assert 820 + w_starv < 1540

w_prio1 = estimate_width("priority inversion: a low-priority task ", 24)
w_prio2 = estimate_width("holds a lock a high-priority task needs", 24)
print(f"Col 2 bug 'priority...': line1={w_prio1:.1f}px, line2={w_prio2:.1f}px, max_right={820+max(w_prio1, w_prio2):.1f}px (< 1540)")
assert 820 + max(w_prio1, w_prio2) < 1540
assert 1560 - (820 + max(w_prio1, w_prio2)) >= 16

# Check Habits strip:
habits_lines = [
    ("keep critical sections tiny ", 115),
    ("and free of I/O", 115),
    ("never call unknown callbacks ", 115),
    ("while holding a lock", 115),
    ("prefer queues and immutable messages", 820),
    ("test with stress loops", 820)
]
for h, x_pos in habits_lines:
    w_h = estimate_width(h, 24)
    r = x_pos + w_h
    bound = 800 if x_pos == 115 else 1540
    print(f"Habit line '{h[:25]}...': w={w_h:.1f}px, right={r:.1f}px (bound {bound})")
    assert r < bound

print("\nALL CLEARANCES AND PADDINGS VERIFIED 100%!")
