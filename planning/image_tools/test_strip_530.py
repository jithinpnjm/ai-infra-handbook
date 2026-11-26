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

print("--- Right strip width 530 (box: 1030 to 1560) ---")
# 530 px wide box. Left padding = 20, right padding = 20. Available = 490 px.
# 490 / 14.4 = 34.0 chars
for m in metrics:
    lines = wrap_text(m, 34)
    print(f"Metric ({len(lines)} lines):")
    for l in lines:
        print(f"   [{len(l):2d} ch, {len(l)*14.4:5.1f}px] '{l}'")
