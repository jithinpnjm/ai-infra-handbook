import re

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

metrics = [
    "Outcome metrics to read first",
    "throughput (tokens/s or samples/s per GPU and aggregate)",
    "step time breakdown: data wait, H2D, forward, backward, exposed communication, optimizer, checkpoint",
    "MFU",
    "scaling efficiency = throughput(N) / (N x throughput(1))",
    "goodput = GPU-hours of useful work / GPU-hours paid, excluding restarts, failures, checkpoint stalls, stragglers and idle waiting",
    "cost: USD per million tokens or per training run"
]

for w in [480, 500, 520, 540, 550, 580]:
    pad = 32
    avail = w - pad
    max_c = int(avail / 14.4)
    total_lines = 0
    print(f"\n--- Width {w} (avail {avail}px, max_c={max_c}) ---")
    for m in metrics:
        lines = wrap_text(m, max_c)
        total_lines += len(lines)
        # print max line len
        max_l = max(len(l) for l in lines)
        print(f"  [{len(lines)} lines, max={max_l}ch/{max_l*14.4:.1f}px] {lines[0]}...")
    print(f"Total lines: {total_lines}")
