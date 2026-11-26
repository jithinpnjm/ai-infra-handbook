def wrap_text(text, max_chars):
    words = text.split(' ')
    lines = []
    current_line = []
    current_len = 0
    for w in words:
        w_len = len(w)
        if not current_line:
            current_line.append(w)
            current_len = w_len
        elif current_len + 1 + w_len <= max_chars:
            current_line.append(w)
            current_len += 1 + w_len
        else:
            lines.append(' '.join(current_line))
            current_line = [w]
            current_len = w_len
    if current_line:
        lines.append(' '.join(current_line))
    return lines

side_panel_labels = [
    "xDS APIs for listeners, routes, clusters, endpoints and secrets",
    "least-request with P2C, ring-hash and Maglev",
    "slow start windows",
    "outlier detection",
    "locality-weighted balancing",
    "panic thresholds: when too many hosts are unhealthy, spread traffic to all rather than overload the few that remain",
    "retry budgets, hedging, rate limiting",
    "connection draining on listener updates",
    "admin interface /clusters and /stats",
    "Istio, Contour, Envoy Gateway, Gloo, Ambassador and many cloud edges"
]

print("--- Side panel with max_chars = 24 ---")
for l in side_panel_labels:
    lines = wrap_text(l, 24)
    print(f"Original: {l}")
    for line in lines:
        print(f"  [{len(line)} chars, {len(line)*14.4:.1f}px] {line}")
