def test_panels():
    panel_w = 740
    inner_w = 740 - 48 # 692 px available for full width row

    print("=== LEFT PANEL: Watch per backend ===")
    metrics = [
        "request counts",
        "in-flight requests",
        "queue time",
        "error and retry rates",
        "TTFT and ITL percentiles",
        "ejection events",
        "hot-backend alerts",
        "trace each request across the gateway, the router and the engine"
    ]
    for m in metrics:
        lw = len(m) * 0.6 * 24
        print(f"  len={len(m):2d}, lw={lw:5.1f}px | '{m}'")

    print("\n=== RIGHT PANEL: Streaming hygiene ===")
    hygiene = [
        "disable proxy buffering for SSE",
        "read and stream-idle timeouts above the maximum generation time",
        "heartbeats",
        "avoid Connection: close",
        "HTTP/2 end to end where possible",
        "measure time-to-first-token (TTFT) and inter-token latency at the proxy with $upstream_response_time or Envoy stats"
    ]
    for h in hygiene:
        lw = len(h) * 0.6 * 24
        print(f"  len={len(h):3d}, lw={lw:5.1f}px | '{h}'")

test_panels()
