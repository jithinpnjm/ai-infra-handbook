import xml.etree.ElementTree as ET

# Strict padding audit for test_candidate_gpu_starvation.svg
tree = ET.parse("test_candidate_gpu_starvation.svg")
root = tree.getroot()

boxes = [
    # Top Panel
    {
        "name": "Top Panel",
        "box": (40, 150, 1520, 95),
        "align": "middle",
        "lines": [
            ("idle gap (bubble): time between kernels or collectives", 24, 205, 800)
        ]
    },
    # Row 1
    {
        "name": "Row 1",
        "box": (40, 260, 1040, 114),
        "align": "left",
        "lines": [
            ("Is the data loader the bottleneck? Empty queue, busy", 24, 308, 180),
            ("workers, a busy iostat, a slow network filesystem", 24, 342, 180)
        ]
    },
    # Row 2
    {
        "name": "Row 2",
        "box": (40, 384, 1040, 114),
        "align": "left",
        "lines": [
            ("Is the CPU the limiter? Single-thread Python launch overhead,", 24, 432, 180),
            ("torch ops launching tiny kernels", 24, 466, 180),
            ("fix: CUDA graphs or compile", 24, 466, 670)
        ]
    },
    # Row 3
    {
        "name": "Row 3",
        "box": (40, 508, 1040, 114),
        "align": "left",
        "lines": [
            ("Is host memory pinned, is the PCIe link at x16, is", 24, 556, 180),
            ("the NUMA placement right?", 24, 590, 180)
        ]
    },
    # Row 4
    {
        "name": "Row 4",
        "box": (40, 632, 1040, 114),
        "align": "left",
        "lines": [
            ("Is communication exposed, meaning not overlapped", 24, 680, 180),
            ("with compute?", 24, 714, 180)
        ]
    },
    # Row 5
    {
        "name": "Row 5",
        "box": (40, 756, 1040, 114),
        "align": "left",
        "lines": [
            ("Is a straggler rank late: thermal throttle, bad", 24, 804, 180),
            ("link, noisy neighbour?", 24, 838, 180)
        ]
    },
    # Row 6
    {
        "name": "Row 6",
        "box": (40, 880, 1040, 114),
        "align": "left",
        "lines": [
            ("Is the checkpoint blocking the step?", 24, 945, 180)
        ]
    },
    # Row 7
    {
        "name": "Row 7",
        "box": (40, 1004, 1040, 114),
        "align": "left",
        "lines": [
            ("Is GPU-Util high while SM activity is low? Many", 24, 1052, 180),
            ("small kernels", 24, 1086, 180)
        ]
    },
    # Right Strip
    {
        "name": "Right Strip",
        "box": (1110, 260, 450, 858),
        "align": "left",
        "lines": [
            ("Outcome metrics", 30, 308, 1134),
            ("to read first", 30, 344, 1134),
            ("throughput (tokens/s or", 24, 398, 1134),
            ("samples/s per GPU and", 24, 426, 1134),
            ("aggregate)", 24, 454, 1134),
            ("step time breakdown: data", 24, 496, 1134),
            ("wait, H2D, forward,", 24, 524, 1134),
            ("backward, exposed", 24, 552, 1134),
            ("communication, optimizer,", 24, 580, 1134),
            ("checkpoint", 24, 608, 1134),
            ("MFU", 24, 650, 1134),
            ("scaling efficiency =", 24, 692, 1134),
            ("throughput(N) / (N x", 24, 720, 1134),
            ("throughput(1))", 24, 748, 1134),
            ("goodput = GPU-hours of", 24, 790, 1134),
            ("useful work / GPU-hours", 24, 818, 1134),
            ("paid, excluding restarts,", 24, 846, 1134),
            ("failures, checkpoint", 24, 874, 1134),
            ("stalls, stragglers and", 24, 902, 1134),
            ("idle waiting", 24, 930, 1134),
            ("cost: USD per million", 24, 972, 1134),
            ("tokens or per training run", 24, 1000, 1134)
        ]
    },
    # Bottom Bar
    {
        "name": "Bottom Bar",
        "box": (40, 1128, 1520, 58),
        "align": "middle",
        "lines": [
            ("Answer each question with a measurement rather than an opinion", 24, 1168, 800)
        ]
    }
]

all_pass = True
for b in boxes:
    bx, by, bw, bh = b["box"]
    print(f"\nChecking {b['name']}: box=({bx}, {by}, {bw}, {bh})")
    for txt, fs, baseline, anchor_x in b["lines"]:
        line_w = len(txt) * fs * 0.6
        if b["align"] == "middle":
            t_left = anchor_x - line_w / 2
            t_right = anchor_x + line_w / 2
        else:
            t_left = anchor_x
            t_right = anchor_x + line_w
        
        pad_l = t_left - bx
        pad_r = (bx + bw) - t_right
        pad_t = (baseline - fs) - by
        pad_b = (by + bh) - baseline
        
        ok_l = pad_l >= 16
        ok_r = pad_r >= 16
        ok_t = pad_t >= 16
        ok_b = pad_b >= 16
        
        if not (ok_l and ok_r and ok_t and ok_b):
            all_pass = False
            print(f"  FAILED: '{txt}'")
            print(f"    pad_l={pad_l:.1f} ({ok_l}), pad_r={pad_r:.1f} ({ok_r}), pad_t={pad_t:.1f} ({ok_t}), pad_b={pad_b:.1f} ({ok_b})")
        else:
            print(f"  OK: '{txt[:30]}...' pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")

assert all_pass, "Some boxes failed padding check!"
print("\nALL BOXES PASSED STRICT >= 16PX PADDING AUDIT!")
