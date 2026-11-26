import re
import xml.etree.ElementTree as ET

def check_line(desc, text, fs, box_l, box_r, anchor, tx, is_mono=False):
    mult = 0.62 if is_mono else 0.6
    w = len(text) * fs * mult
    if anchor == 'middle':
        l = tx - w / 2.0
        r = tx + w / 2.0
    elif anchor == 'start':
        l = tx
        r = tx + w
    else:
        l = tx - w
        r = tx
    pad_l = l - box_l
    pad_r = box_r - r
    min_pad = min(pad_l, pad_r)
    print(f"[{'PASS' if min_pad >= 16.0 else 'FAIL'}] {desc:30s}: min_pad={min_pad:5.1f}px (w={w:5.1f}px, box_w={box_r-box_l}px) | '{text}'")
    assert min_pad >= 16.0, f"FAILED padding for {desc}: {min_pad:.1f} < 16.0"

print("--- Testing Ask first chips ---")
# Col 1: 65..775 (w=710)
# Col 2: 815..1535 (w=720)
check_line("Chip 1", "Fleet: 2,000 nodes of 8 GPUs", 24, 65, 775, 'middle', 420)
check_line("Chip 2", "Failure rate: 5 percent of GPUs per year", 24, 815, 1535, 'middle', 1175)
check_line("Chip 3", "Idle or serving: both", 24, 65, 775, 'middle', 420)
check_line("Chip 4 line 1", "Customer notices: errors or slow tokens", 24, 815, 1535, 'middle', 1175)
check_line("Chip 4 line 2", "after about 15 minutes", 24, 815, 1535, 'middle', 1175)

print("\n--- Testing Calculation Ladder 4 steps ---")
# Step 1: 40..350 (w=310)
# Step 2: 435..745 (w=310)
# Step 3: 830..1140 (w=310)
# Step 4: 1225..1560 (w=335)
check_line("Step 1 line 1", "GPUs:", 28, 40, 350, 'middle', 195)
check_line("Step 1 line 2", "2,000 x 8 = 16,000", 24, 40, 350, 'middle', 195)

check_line("Step 2 line 1", "Failures per day:", 26, 435, 745, 'middle', 590)
check_line("Step 2 line 2", "16,000 x 0.05 / 365", 24, 435, 745, 'middle', 590)
check_line("Step 2 line 3", "= 2.19", 26, 435, 745, 'middle', 590)

check_line("Step 3 line 1", "Series at 40 fields", 24, 830, 1140, 'middle', 985)
check_line("Step 3 line 2", "per GPU:", 24, 830, 1140, 'middle', 985)
check_line("Step 3 line 3", "16,000 x 40", 24, 830, 1140, 'middle', 985)
check_line("Step 3 line 4", "= 640,000", 26, 830, 1140, 'middle', 985)

check_line("Step 4 line 1", "Samples per second", 24, 1225, 1560, 'middle', 1392)
check_line("Step 4 line 2", "at a 15 s scrape:", 24, 1225, 1560, 'middle', 1392)
check_line("Step 4 line 3", "640,000 / 15", 24, 1225, 1560, 'middle', 1392)
check_line("Step 4 line 4", "= 42,667", 26, 1225, 1560, 'middle', 1392)

print("\n--- Testing Final Result Card ---")
# Box: x = 200..1400 (w=1200)
check_line("Final Result line 1", "Requests spared per event: 2 x 60 x 13 = 1,560,", 26, 200, 1400, 'middle', 800)
check_line("Final Result line 2", "detect at 2 minutes against 15", 26, 200, 1400, 'middle', 800)

print("\n--- Testing Grey Note ---")
# Note: full canvas x = 40..1560 (w=1520)
check_line("Note line", "Every input is an assumption, not a measurement.", 26, 40, 1560, 'middle', 800)

print("\n--- Testing Caption ---")
check_line("Caption line", "The detection time has to beat the moment the customer notices.", 28, 40, 1560, 'middle', 800)
