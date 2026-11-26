# Let's check all text boxes and their inner texts to ensure >= 16px padding everywhere
checks = [
    # (box_x, box_y, box_w, box_h, text, font_size, is_bold, lines)
    (40, 125, 150, 120, "Client", 30, True, ["Client"]),
    (50, 255, 330, 135, "annotation", 24, False, ["where pinning", "happens at L4", "L7 or client-side", "balancing fixes it"]),
    (400, 125, 275, 265, "Gateway", 24, True, ["anycast or ECMP", "to a fleet of L4", "and L7 gateways", "(BGP VIP, BFD)"]),
    (705, 125, 285, 265, "TLS", 24, True, ["TLS termination", "and L7 routing", "with per-request,", "per-tenant policy"]),
    (1020, 125, 250, 265, "Picker", 24, True, ["load- and", "cache-aware", "endpoint picker"]),
    (1300, 125, 260, 265, "Pods", 24, True, ["inference pods", "with readiness,", "drain and GPU", "health", "integration"]),
    (40, 415, 740, 430, "Watch per backend", 30, True, ["Watch per backend"]),
    (65, 475, 335, 52, "request counts", 24, False, ["request counts"]),
    (420, 475, 335, 52, "in-flight requests", 24, False, ["in-flight requests"]),
    (65, 539, 335, 58, "queue time", 24, False, ["queue time"]),
    (420, 539, 335, 58, "error and retry rates", 24, False, ["error and", "retry rates"]),
    (65, 609, 335, 58, "TTFT and ITL percentiles", 24, False, ["TTFT and ITL", "percentiles"]),
    (420, 609, 335, 58, "ejection events", 24, False, ["ejection events"]),
    (65, 679, 690, 50, "hot-backend alerts", 24, False, ["hot-backend alerts"]),
    (65, 741, 690, 86, "trace each request", 24, False, ["trace each request across the gateway,", "the router and the engine"]),
    (845, 435, 690, 54, "disable proxy buffering for SSE", 24, False, ["disable proxy buffering for SSE"]),
    (845, 501, 690, 76, "read and stream-idle timeouts", 24, False, ["read and stream-idle timeouts", "above the maximum generation time"]),
    (845, 589, 240, 54, "heartbeats", 24, False, ["heartbeats"]),
    (1105, 589, 430, 54, "avoid Connection: close", 24, False, ["avoid Connection: close"]),
    (845, 655, 690, 54, "HTTP/2 end to end where possible", 24, False, ["HTTP/2 end to end where possible"]),
    (845, 721, 690, 106, "measure time-to-first-token", 24, False, ["measure time-to-first-token (TTFT) and", "inter-token latency at the proxy with", "$upstream_response_time or Envoy stats"]),
    (40, 865, 1520, 240, "strip", 24, False, [
        "BGP convergence sets how quickly a failed node's traffic moves; BFD detects in under a second;",
        "resilient or consistent hashing in the router moves only the failed node's flows;",
        "announce the VIP only while the node can serve; a route change can move a flow to a different site,",
        "which breaks long-lived TCP; fabric ECMP caveats: elephant flows,",
        "RoCE varies UDP source ports per QP, tunnels need inner-header hashing,",
        "adaptive routing reacts to load"
    ]),
    (40, 1125, 1520, 52, "bottom bar", 30, True, ["Decide your failover budget first"])
]

all_passed = True
for bx, by, bw, bh, name, fs, bold, lines in checks:
    print(f"\nChecking '{name}' (bw={bw}, bh={bh}):")
    for l in lines:
        factor = 0.62 if '$' in l else 0.6
        lw = len(l) * factor * fs
        pad_x = (bw - lw) / 2
        ok = (pad_x >= 16)
        if not ok:
            all_passed = False
        print(f"  [{'OK' if ok else 'FAIL'}] pad_x={pad_x:5.1f}px (lw={lw:6.1f}px) | '{l}'")

print(f"\nALL PADDING CHECKS PASSED: {all_passed}")
