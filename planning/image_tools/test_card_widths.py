import math

# Conservative width estimates:
# sans: 0.6 * font_size per character
# monospace: 0.62 * font_size per character

def check_line(text, font_size=24, is_mono=False):
    factor = 0.62 if is_mono else 0.6
    w = len(text) * font_size * factor
    return w

lines_map = {
    "Lane 1 Header": [
        ("Kernel cgroup OOM kill", 32, False)
    ],
    "Lane 1 Step 1": [
        ("memory.current reaches memory.max", 24, True),
        ("(set from limits.memory)", 24, True)
    ],
    "Lane 1 Step 2": [
        ("Linux kernel, synchronous, SIGKILL", 26, False)
    ],
    "Lane 1 Step 3": [
        ("container exits OOMKilled, exit code 137;", 24, False),
        ("kubelet restarts it in place if", 24, False),
        ("restartPolicy allows;", 24, False),
        ("memory.events shows oom and oom_kill", 24, True)
    ],
    "Lane 2 Header": [
        ("Kubelet node-pressure eviction", 32, False)
    ],
    "Lane 2 Step 1": [
        ("node-wide memory.available below", 24, True),
        ("evictionHard (for example 100Mi) or", 24, True),
        ("nodefs.available below 10 percent", 24, True)
    ],
    "Lane 2 Step 2": [
        ("kubelet eviction manager", 26, False),
        ("in user space", 26, False)
    ],
    "Lane 2 Step 3": [
        ("BestEffort, then Burstable", 26, False),
        ("over requests, then Guaranteed", 26, False)
    ],
    "Lane 2 Step 4": [
        ("whole pod Failed with Reason Evicted;", 24, False),
        ("owning controller reschedules", 24, False)
    ],
    "Footer": [
        ("Eviction ignores PodDisruptionBudgets; BestEffort and Burstable", 24, False),
        ("over requests are preferred OOM victims via oom_score_adj", 24, False)
    ]
}

max_allowed_card_text_w = 530 # 665 - 100 - 25 - 10

print(f"Max allowed text width: {max_allowed_card_text_w}px\n")
for node, lines in lines_map.items():
    print(f"=== {node} ===")
    for text, fs, is_mono in lines:
        w = check_line(text, fs, is_mono)
        status = "OK" if w <= (1400 if node == "Footer" or "Header" in node else max_allowed_card_text_w) else "FAIL"
        print(f"  [{status}] ({w:5.1f}px / len {len(text):2d}) '{text}'")
