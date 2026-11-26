def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    current = []
    current_len = 0
    for w in words:
        if current_len + len(w) + (1 if current else 0) <= max_chars:
            current.append(w)
            current_len += len(w) + (1 if len(current) > 1 else 0)
        else:
            lines.append(" ".join(current))
            current = [w]
            current_len = len(w)
    if current:
        lines.append(" ".join(current))
    return lines

strip_items = [
    {
        "label": "Outcome metrics to read first",
        "header": True,
        "lines": ["Outcome metrics", "to read first"]
    },
    {
        "label": "throughput (tokens/s or samples/s per GPU and aggregate)",
        "lines": wrap_text("throughput (tokens/s or samples/s per GPU and aggregate)", 26)
    },
    {
        "label": "step time breakdown: data wait, H2D, forward, backward, exposed communication, optimizer, checkpoint",
        "lines": wrap_text("step time breakdown: data wait, H2D, forward, backward, exposed communication, optimizer, checkpoint", 26)
    },
    {
        "label": "MFU",
        "lines": ["MFU"]
    },
    {
        "label": "scaling efficiency = throughput(N) / (N x throughput(1))",
        "lines": wrap_text("scaling efficiency = throughput(N) / (N x throughput(1))", 26)
    },
    {
        "label": "goodput = GPU-hours of useful work / GPU-hours paid, excluding restarts, failures, checkpoint stalls, stragglers and idle waiting",
        "lines": wrap_text("goodput = GPU-hours of useful work / GPU-hours paid, excluding restarts, failures, checkpoint stalls, stragglers and idle waiting", 26)
    },
    {
        "label": "cost: USD per million tokens or per training run",
        "lines": wrap_text("cost: USD per million tokens or per training run", 26)
    }
]

right_box = (1110, 260, 450, 858)
bx, by, bw, bh = right_box

current_y = by + 48
item_blocks = []

for idx, item in enumerate(strip_items):
    lines = item["lines"]
    is_hdr = item.get("header", False)
    fs = 30 if is_hdr else 24
    
    bls = []
    dy = 36 if is_hdr else 28
    for l_idx, line in enumerate(lines):
        bls.append(current_y)
        current_y += dy
    current_y += 14 # gap between metrics
    
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
