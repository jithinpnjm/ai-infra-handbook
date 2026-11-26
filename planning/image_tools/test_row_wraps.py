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

# Row width available: 780 px
# At 24px, 0.6 * 24 = 14.4 px/char -> 780 / 14.4 = 54 chars max!
# Let's test max_chars = 52

rows = [
    (1, "Is the data loader the bottleneck? Empty queue, busy workers, a busy iostat, a slow network filesystem"),
    (2, "Is the CPU the limiter? Single-thread Python launch overhead, torch ops launching tiny kernels"),
    (3, "Is host memory pinned, is the PCIe link at x16, is the NUMA placement right?"),
    (4, "Is communication exposed, meaning not overlapped with compute?"),
    (5, "Is a straggler rank late: thermal throttle, bad link, noisy neighbour?"),
    (6, "Is the checkpoint blocking the step?"),
    (7, "Is GPU-Util high while SM activity is low? Many small kernels")
]

for num, r in rows:
    lines = wrap_text(r, 52)
    print(f"Row {num} ({len(lines)} lines):")
    for l in lines:
        print(f"   [{len(l):2d} ch, {len(l)*14.4:5.1f}px] '{l}'")
