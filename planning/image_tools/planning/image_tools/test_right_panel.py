def calc_right_panel():
    y = 445 # after header
    items = [
        ("disable proxy buffering for SSE", 50),
        ("read and stream-idle timeouts above the maximum generation time", 65),
        ("heartbeats / avoid Connection: close", 50),
        ("HTTP/2 end to end where possible", 50),
        ("measure time-to-first-token (TTFT) and inter-token latency at the proxy with $upstream_response_time or Envoy stats", 90)
    ]
    curr_y = 475
    gap = 12
    for name, h in items:
        print(f"y={curr_y}..{curr_y+h} (h={h}) | {name[:40]}")
        curr_y += h + gap
    print(f"Total end y: {curr_y - gap}, Panel bottom: 835")

calc_right_panel()
