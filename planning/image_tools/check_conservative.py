import xml.etree.ElementTree as ET

# Setup boxes geometry:
boxes = {
    "setup-strip": {"x": 40, "y": 100, "w": 1520, "h": 160, "icon_r": 126},
    "problem-1": {"x": 40, "y": 300, "w": 740, "h": 265, "icon_r": 126},
    "problem-2": {"x": 40, "y": 605, "w": 740, "h": 265, "icon_r": 126},
    "fix-column": {"x": 820, "y": 300, "w": 740, "h": 570, "icon_r": 908},
    "footer-takeaway": {"x": 40, "y": 910, "w": 1520, "h": 130, "icon_r": 126}
}

# Lines per box:
lines = {
    "setup-strip": [
        "short burst every six minutes;",
        "autoscaler removes replicas after each burst",
        "and adds them back a few minutes later;",
        "users report streams that stop halfway"
    ],
    "problem-1": [
        "flapping wastes cold starts:",
        "in-flight policy with no window",
        "starts 130 replicas in an hour",
        "and reverses direction 19 times;",
        "with a 300 s window it starts 13",
        "and reverses once"
    ],
    "problem-2": [
        "scale-down without a drain cuts streams:",
        "waiting-queue policy with",
        "no drain cut 168 streams"
    ],
    "fix-column": [
        "lengthen the window beyond the",
        "cold start and slow the scale-down",
        "(removes most cold starts);",
        "then add the drain stack",
        "from section 7: grace period,",
        "preStop pause, engine drain,",
        "PodDisruptionBudget"
    ],
    "footer-takeaway": [
        "fixing only flapping leaves users on a removed pod unprotected;",
        "fixing only the drain keeps the waste; all counts are simulator output"
    ]
}

start_xs = {
    "setup-strip": 156,
    "problem-1": 156,
    "problem-2": 156,
    "fix-column": 936,
    "footer-takeaway": 156
}

fs = 25.0

print("=== CONSERVATIVE FORMULA CHECK (len * 0.6 * 25) ===")
for b_id, b_info in boxes.items():
    sx = start_xs[b_id]
    b_right = b_info["x"] + b_info["w"]
    icon_right = b_info["icon_r"]
    
    assert sx - icon_right >= 16, f"[{b_id}] text start_x {sx} too close to icon {icon_right}"
    
    for l in lines[b_id]:
        est_w = len(l) * 0.6 * fs
        end_x = sx + est_w
        pad_r = b_right - end_x
        print(f"[{b_id:15s}] len={len(l):2d} est_w={est_w:5.1f} end_x={end_x:6.1f} box_r={b_right} pad_r={pad_r:5.1f} | '{l}'")
        assert pad_r >= 16, f"[{b_id}] OVERFLOW! pad_r={pad_r} < 16 for '{l}'"

print("\nALL CONSERVATIVE FORMULA CHECKS PASSED WITH >= 16PX PADDING!")
