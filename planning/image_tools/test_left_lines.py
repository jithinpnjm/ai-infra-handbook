labels_left = [
    ("Did the server receive the request?",
     ["Did the server receive", "the request?"]),
    ("Did the request leave the client at all?",
     ["Did the request leave the", "client at all?"]),
    ("Traffic inside a pod",
     ["Traffic inside a pod"]),
    ("Traffic crossing between namespaces",
     ["Traffic crossing between", "namespaces"]),
    ("Need the wire itself, independent of the host stack",
     ["Need the wire itself,", "independent of the host stack"]),
    ("RoCE or traffic the kernel does not see",
     ["RoCE or traffic the", "kernel does not see"]),
    ("Where was the packet dropped, without copying it?",
     ["Where was the packet dropped,", "without copying it?"])
]

avail_w = 524  # 640 - 116
print("=== LEFT SIDE (avail_w = 524) at 28px ===")
for full, lines in labels_left:
    fs = 28  # let's test 28px or 30px
    factor = 0.6
    print(f"Label ({len(lines)} lines):")
    for l in lines:
        w = len(l) * fs * factor
        pad = avail_w - w
        assert pad >= 16, f"FAIL: '{l}' pad={pad:.1f}px"
        print(f"   '{l}' -> {len(l)}c, {w:.1f}px, pad={pad:.1f}px")
