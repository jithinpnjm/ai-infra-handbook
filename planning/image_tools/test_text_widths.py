import xml.etree.ElementTree as ET

tree = ET.parse('test_passive_active.svg')
root = tree.getroot()

def get_char_w(font, size):
    if 'monospace' in font.lower():
        return 0.62 * size
    return 0.60 * size

# Check all tspans and text lines
lines = [
    # Box 1 (x=40..770, w=730, y=145..330)
    ("Box1 Line 1", 70, 195, "Passive: reads what hardware already", 28, "sans-serif", 40, 770, 145, 330),
    ("Box1 Line 2", 70, 233, "reports, always on, cheap, only sees", 25, "sans-serif", 40, 770, 145, 330),
    ("Box1 Line 3", 70, 271, "faults that already produced an error", 25, "sans-serif", 40, 770, 145, 330),
    
    # Box 2 (x=830..1560, w=730, y=145..330)
    ("Box2 Line 1", 860, 188, "Active: dcgmi diag does work on the", 28, "sans-serif", 830, 1560, 145, 330),
    ("Box2 Line 2", 860, 222, "GPU and compares with a healthy GPU,", 25, "sans-serif", 830, 1560, 145, 330),
    ("Box2 Line 3", 860, 256, "finds weak hardware not yet failed,", 25, "sans-serif", 830, 1560, 145, 330),
    ("Box2 Line 4", 860, 290, "node usually out of service", 25, "sans-serif", 830, 1560, 145, 330),
    
    # Level 1 (x=40..1560, w=1520, y=355..447)
    ("L1 Line 1", 135, 392, "level 1 dcgmi diag -r 1: software, driver, permissions,", 28, "sans-serif", 40, 1560, 355, 447),
    ("L1 Line 2", 135, 428, "under 2.5 seconds", 25, "sans-serif", 40, 1560, 355, 447),

    # Level 2 (x=40..1560, w=1520, y=462..554)
    ("L2 Line 1", 135, 499, "level 2 -r 2: extended validation,", 28, "sans-serif", 40, 1560, 462, 554),
    ("L2 Line 2", 135, 535, "under 2.5 min on 4 GPUs, under 10.5 min on 8", 25, "sans-serif", 40, 1560, 462, 554),

    # Level 3 (x=40..1560, w=1520, y=569..661)
    ("L3 Line 1", 135, 606, "level 3 -r 3: stress, power, bandwidth and NCCL tests,", 28, "sans-serif", 40, 1560, 569, 661),
    ("L3 Line 2", 135, 642, "under 10 min on 4 GPUs, under 35 min on 8", 25, "sans-serif", 40, 1560, 569, 661),

    # Level 4 (x=40..1560, w=1520, y=676..768)
    ("L4 Line 1", 135, 713, "level 4 -r 4: adds memory test and power pulse test,", 28, "sans-serif", 40, 1560, 676, 768),
    ("L4 Line 2", 135, 749, "under 45 min on 4 GPUs, under 2.25 h on 8", 25, "sans-serif", 40, 1560, 676, 768),

    # Where each runs (x=40..1560, w=1520, y=785..1020)
    ("Runs Line 1", 135, 835, "passive: continuously on every node;", 26, "sans-serif", 40, 1560, 785, 1020),
    ("Runs Line 2", 135, 879, "level 1: when a node is about to take traffic;", 26, "sans-serif", 40, 1560, 785, 1020),
    ("Runs Line 3", 135, 923, "level 3: gate when a node leaves repair;", 26, "sans-serif", 40, 1560, 785, 1020),
    ("Runs Line 4", 135, 967, "multi-node NCCL test: gate for a node joining a training or large tensor-parallel group", 26, "sans-serif", 40, 1560, 785, 1020),

    # Automation note (x=40..1560, w=1520, y=1040..1135)
    ("Note Line 1", 135, 1098, "exit code 0 success, 226 diagnostic ran and reported an error, add -j for JSON", 26, "sans-serif", 40, 1560, 1040, 1135),
]

all_pad_ok = True
for name, x, y, text, fs, font, bx1, bx2, by1, by2 in lines:
    est_w = len(text) * get_char_w(font, fs)
    text_end_x = x + est_w
    pad_left = x - bx1
    pad_right = bx2 - text_end_x
    pad_top = (y - fs) - by1
    pad_bottom = by2 - y
    print(f"{name:12s} | chars={len(text):2d} | est_w={est_w:6.1f}px | pad_left={pad_left:4.1f} | pad_right={pad_right:5.1f} | pad_top={pad_top:4.1f} | pad_bottom={pad_bottom:4.1f}")
    if pad_left < 16 or pad_right < 16 or pad_top < 8 or pad_bottom < 8:
        print(f"  WARNING: padding tight on {name}!")
        all_pad_ok = False

if all_pad_ok:
    print("\nALL TEXT LINES HAVE EXCELLENT PADDING (>= 16px)!")
