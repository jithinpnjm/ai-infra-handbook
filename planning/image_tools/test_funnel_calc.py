# Let's test funnel layout and text wrapping calculations
def check_text_fit(lines, font_size, box_width, padding=16):
    max_w = 0
    for line in lines:
        w = len(line) * 0.60 * font_size
        if w > max_w:
            max_w = w
    avail = box_width - 2 * padding
    fits = max_w <= avail
    print(f"Max text width: {max_w:.1f}px, Avail width: {avail:.1f}px, Fits: {fits}")
    return fits

print("Step 1:")
check_text_fit(["Quantify: throughput, latency percentiles,", "retransmit rate, against baseline and line rate or BDP"], 24, 1000)

print("Step 2:")
check_text_fit(["Find the limit: ss -ti limiter flags, CPU and", "softirq, NIC drops, PFC, ECN, MTU"], 24, 900)

print("Step 3:")
check_text_fit(["Find the segment: iperf3 or ib_write_bw", "between pairs, halving the path"], 24, 800)

print("Step 4:")
check_text_fit(["Loss or latency: nstat and tcpretrans for", "loss, ss -ti and ping for RTT"], 24, 700)

print("Step 5:")
check_text_fit(["One flow or all flows: ECMP hash collisions,", "elephant flows, single-core limits"], 24, 650)

print("Side box:")
check_text_fit(["Step 6:", "compare with a", "healthy node"], 24, 280)
