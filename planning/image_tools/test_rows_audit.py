import xml.etree.ElementTree as ET

# Let's verify all 7 rows
# Box x = 40, width = 1040 (x: 40 to 1080)
# Height = 114 each
# Gaps = 10 px
# Row y starts at: 260
row_h = 114
gap = 10
y_start = 260

rows_data = [
    {
        "num": "1",
        "label": "Is the data loader the bottleneck? Empty queue, busy workers, a busy iostat, a slow network filesystem",
        "lines": [
            "Is the data loader the bottleneck? Empty queue, busy",
            "workers, a busy iostat, a slow network filesystem"
        ]
    },
    {
        "num": "2",
        "label": "Is the CPU the limiter? Single-thread Python launch overhead, torch ops launching tiny kernels",
        "lines": [
            "Is the CPU the limiter? Single-thread Python launch overhead,",
            "torch ops launching tiny kernels"
        ],
        "fix": "fix: CUDA graphs or compile",
        "fix_x": 670
    },
    {
        "num": "3",
        "label": "Is host memory pinned, is the PCIe link at x16, is the NUMA placement right?",
        "lines": [
            "Is host memory pinned, is the PCIe link at x16, is",
            "the NUMA placement right?"
        ]
    },
    {
        "num": "4",
        "label": "Is communication exposed, meaning not overlapped with compute?",
        "lines": [
            "Is communication exposed, meaning not overlapped",
            "with compute?"
        ]
    },
    {
        "num": "5",
        "label": "Is a straggler rank late: thermal throttle, bad link, noisy neighbour?",
        "lines": [
            "Is a straggler rank late: thermal throttle, bad",
            "link, noisy neighbour?"
        ],
        "orange": True
    },
    {
        "num": "6",
        "label": "Is the checkpoint blocking the step?",
        "lines": [
            "Is the checkpoint blocking the step?"
        ]
    },
    {
        "num": "7",
        "label": "Is GPU-Util high while SM activity is low? Many small kernels",
        "lines": [
            "Is GPU-Util high while SM activity is low? Many",
            "small kernels"
        ]
    }
]

for i, r in enumerate(rows_data):
    by = y_start + i * (row_h + gap)
    bx, bw, bh = 40, 1040, row_h
    print(f"\n--- Row {r['num']} (y={by}..{by+bh}) ---")
    
    # Check lines
    num_lines = len(r['lines'])
    if num_lines == 1:
        baselines = [by + 65]
    else:
        baselines = [by + 48, by + 82]
    
    for line, bl in zip(r['lines'], baselines):
        w = len(line) * 24 * 0.6
        pad_l = 180 - bx
        pad_r = (bx + bw) - (180 + w)
        pad_t = (bl - 24) - by
        pad_b = (by + bh) - bl
        print(f"  Line: '{line}' ({len(line)}ch, {w:.1f}px)")
        print(f"    pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
        assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16, "Padding failed!"
        
    if "fix" in r:
        fix_txt = r["fix"]
        fix_x = r["fix_x"]
        w_fix = len(fix_txt) * 24 * 0.6
        bl = by + 82
        pad_l = fix_x - bx
        pad_r = (bx + bw) - (fix_x + w_fix)
        pad_t = (bl - 24) - by
        pad_b = (by + bh) - bl
        print(f"  Fix: '{fix_txt}' ({len(fix_txt)}ch, {w_fix:.1f}px)")
        print(f"    pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
        assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16, "Fix padding failed!"

print("\nALL 7 ROWS PASSED PADDING AUDIT!")
