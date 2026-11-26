#!/usr/bin/env python3

# Canvas 1600 x 1060
# Row 1: y = 125 .. 435 (h = 310)
# Row 2: y = 520 .. 840 (h = 320)
# Takeaway: y = 880 .. 960 (h = 80)
# Caption: y = 1010

items = [
    # desc, bx, by, bw, bh, text, ftype, fsize, tx, ty
    ("Title", 0, 0, 1600, 100, "The six-step estimation chain from weights to GPUs", "sans", 48, 800, 68),
    
    # Box 1
    ("Box 1 Title", 50, 125, 460, 310, "Weights memory", "sans", 30, 280, 235),
    ("Box 1 In L1", 70, 275, 420, 140, "parameters x bytes", "mono", 24, 280, 335),
    ("Box 1 In L2", 70, 275, 420, 140, "per parameter", "mono", 24, 280, 375),
    
    # Box 2
    ("Box 2 Title", 570, 125, 460, 310, "KV cache per request", "sans", 30, 800, 235),
    ("Box 2 In L1", 590, 275, 420, 140, "KV bytes per token x", "mono", 24, 800, 335),
    ("Box 2 In L2", 590, 275, 420, 140, "(prompt + output tokens)", "mono", 24, 800, 375),
    
    # Box 3
    ("Box 3 Title L1", 1090, 125, 460, 310, "Requests that fit", "sans", 30, 1320, 215),
    ("Box 3 Title L2", 1090, 125, 460, 310, "on one GPU", "sans", 30, 1320, 253),
    ("Box 3 In L1", 1110, 275, 420, 140, "GPU memory x 0.9", "mono", 24, 1320, 315),
    ("Box 3 In L2", 1110, 275, 420, 140, "minus weights, divided by", "mono", 24, 1320, 350),
    ("Box 3 In L3", 1110, 275, 420, 140, "KV per request", "mono", 24, 1320, 385),
    
    # Box 4
    ("Box 4 Title L1", 50, 520, 335, 320, "Decode tokens", "sans", 30, 217, 608),
    ("Box 4 Title L2", 50, 520, 335, 320, "per second", "sans", 30, 217, 646),
    ("Box 4 In L1", 68, 675, 299, 145, "batch size and", "mono", 24, 217, 735),
    ("Box 4 In L2", 68, 675, 299, 145, "decode rate", "mono", 24, 217, 775),
    
    # Box 5
    ("Box 5 Title L1", 438, 520, 335, 320, "Requests per", "sans", 30, 605, 608),
    ("Box 5 Title L2", 438, 520, 335, 320, "second per GPU", "sans", 30, 605, 646),
    # Box 5 inner card: y=675, h=145
    ("Box 5 In1 L1", 456, 675, 299, 145, "prefill tokens", "mono", 24, 605, 705),
    ("Box 5 In1 L2", 456, 675, 299, 145, "per second", "mono", 24, 605, 735),
    ("Box 5 In2 L1", 456, 675, 299, 145, "decode tokens", "mono", 24, 605, 770),
    ("Box 5 In2 L2", 456, 675, 299, 145, "per second", "mono", 24, 605, 800),
    
    # Box 6
    ("Box 6 Title L1", 826, 520, 335, 320, "GPUs for QPS,", "sans", 30, 993, 590),
    ("Box 6 Title L2", 826, 520, 335, 320, "plus headroom", "sans", 30, 993, 626),
    ("Box 6 Title L3", 826, 520, 335, 320, "and N+1", "sans", 30, 993, 662),
    ("Box 6 In L1", 844, 680, 299, 140, "demand divided by", "mono", 24, 993, 720),
    ("Box 6 In L2", 844, 680, 299, 140, "requests per", "mono", 24, 993, 755),
    ("Box 6 In L3", 844, 680, 299, 140, "second per GPU", "mono", 24, 993, 790),
    
    # Cost Card
    ("Cost Card L1", 1232, 675, 300, 145, "Cost per", "sans", 30, 1382, 735),
    ("Cost Card L2", 1232, 675, 300, 145, "million tokens", "sans", 30, 1382, 775),
    
    # Takeaway Bar
    ("Takeaway Bar", 50, 880, 1500, 80, "Each box is a ceiling, not a measurement", "sans", 30, 800, 930),
    
    # Caption
    ("Caption", 0, 980, 1600, 70, "Work forward from the inputs, never backward from the answer you want.", "sans", 26, 800, 1020),
]

all_pass = True
for desc, bx, by, bw, bh, text, ftype, fsize, tx, ty in items:
    rate = 0.62 if ftype == "mono" else 0.60
    tw = len(text) * rate * fsize
    pad_L = (tx - tw / 2) - bx
    pad_R = (bx + bw) - (tx + tw / 2)
    pad_T = (ty - fsize * 0.75) - by
    pad_B = (by + bh) - ty
    min_pad_h = min(pad_L, pad_R)
    min_pad_v = min(pad_T, pad_B)
    min_pad = min(min_pad_h, min_pad_v)
    ok = min_pad >= 16
    if not ok: all_pass = False
    print(f"[{'PASS' if ok else 'FAIL'}] {desc:25s}: pad_H={min_pad_h:5.1f}, pad_V={min_pad_v:5.1f} (min={min_pad:5.1f})")

assert all_pass, "Some paddings failed!"
print("\nALL 29 PADDING CHECKS PASSED (min_pad >= 16px)!")
