# Let's test right strip padding
# Box: x = 1110, y = 260, w = 450, h = 858

right_box = (1110, 260, 450, 858)
bx, by, bw, bh = right_box

# Metrics in right strip:
# 1. Header: Outcome metrics to read first
# 2. throughput (tokens/s or samples/s per GPU and aggregate)
# 3. step time breakdown: data wait, H2D, forward, backward, exposed communication, optimizer, checkpoint
# 4. MFU
# 5. scaling efficiency = throughput(N) / (N x throughput(1))
# 6. goodput = GPU-hours of useful work / GPU-hours paid, excluding restarts, failures, checkpoint stalls, stragglers and idle waiting
# 7. cost: USD per million tokens or per training run

# Inside right strip, available width with 20px padding on each side is 410 px.
# 410 / 14.4 = 28.4 chars max.

strip_items = [
    {
        "label": "Outcome metrics to read first",
        "header": True,
        "lines": ["Outcome metrics to read first"]
    },
    {
        "label": "throughput (tokens/s or samples/s per GPU and aggregate)",
        "lines": [
            "throughput (tokens/s or",
            "samples/s per GPU and",
            "aggregate)"
        ]
    },
    {
        "label": "step time breakdown: data wait, H2D, forward, backward, exposed communication, optimizer, checkpoint",
        "lines": [
            "step time breakdown: data",
            "wait, H2D, forward, backward,",
            "exposed communication,",
            "optimizer, checkpoint"
        ]
    },
    {
        "label": "MFU",
        "lines": ["MFU"]
    },
    {
        "label": "scaling efficiency = throughput(N) / (N x throughput(1))",
        "lines": [
            "scaling efficiency =",
            "throughput(N) / (N x",
            "throughput(1))"
        ]
    },
    {
        "label": "goodput = GPU-hours of useful work / GPU-hours paid, excluding restarts, failures, checkpoint stalls, stragglers and idle waiting",
        "lines": [
            "goodput = GPU-hours of useful",
            "work / GPU-hours paid,",
            "excluding restarts, failures,",
            "checkpoint stalls, stragglers",
            "and idle waiting"
        ]
    },
    {
        "label": "cost: USD per million tokens or per training run",
        "lines": [
            "cost: USD per million tokens",
            "or per training run"
        ]
    }
]

# Let's allocate vertical positions inside the strip
# Let's see: total height = 858.
# Header at y = by + 46 (font-size 30 bold)
# Then items: 6 items.
# Let's compute baselines for each line:
current_y = by + 50
item_blocks = []

for idx, item in enumerate(strip_items):
    lines = item["lines"]
    is_hdr = item.get("header", False)
    fs = 30 if is_hdr else 24
    
    if is_hdr:
        bls = [current_y]
        current_y += 45
    else:
        bls = []
        for l_idx, line in enumerate(lines):
            bls.append(current_y)
            current_y += 30
        current_y += 18 # gap between metrics
    
    item_blocks.append((item["label"], lines, bls, fs))

print(f"Total height used: {current_y - by}px out of {bh}px.")
print(f"Bottom margin: {bh - (current_y - by)}px.")

all_pass = True
for label, lines, bls, fs in item_blocks:
    for line, bl in zip(lines, bls):
        w = len(line) * fs * 0.6
        anchor_x = bx + 24
        pad_l = anchor_x - bx
        pad_r = (bx + bw) - (anchor_x + w)
        pad_t = (bl - fs) - by
        pad_b = (by + bh) - bl
        print(f"  [{fs}px] '{line}' ({len(line)}ch, {w:.1f}px): pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
        if not (pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16):
            all_pass = False
            print("    FAILED!")

assert all_pass, "Right strip padding failed!"
print("\nRIGHT STRIP PASSED STRICT PADDING AUDIT!")
