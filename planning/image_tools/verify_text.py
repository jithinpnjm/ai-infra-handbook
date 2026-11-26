# Verify exact text line wrapping and widths

def measure(line, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.6
    return len(line) * fs * factor

card_text_w = 540 # available width

cards = {
    "L1 Trigger": [
        ("memory.current reaches", 24, True),
        ("memory.max (set from", 24, True),
        ("limits.memory)", 24, True)
    ],
    "L1 Actor": [
        ("Linux kernel,", 26, False),
        ("synchronous, SIGKILL", 26, False)
    ],
    "L1 Result": [
        ("container exits OOMKilled,", 24, False),
        ("exit code 137; kubelet restarts", 24, False),
        ("it in place if restartPolicy allows;", 24, False),
        ("memory.events shows oom and", 24, True),
        ("oom_kill", 24, True)
    ],
    "L2 Trigger": [
        ("node-wide memory.available", 24, True),
        ("below evictionHard (for", 24, True),
        ("example 100Mi) or", 24, True),
        ("nodefs.available below 10", 24, True),
        ("percent", 24, True)
    ],
    "L2 Actor": [
        ("kubelet eviction manager", 26, False),
        ("in user space", 26, False)
    ],
    "L2 Ranking": [
        ("BestEffort, then Burstable", 26, False),
        ("over requests, then", 26, False),
        ("Guaranteed", 26, False)
    ],
    "L2 Result": [
        ("whole pod Failed with Reason", 24, False),
        ("Evicted; owning controller", 24, False),
        ("reschedules", 24, False)
    ],
    "Footer": [
        ("Eviction ignores PodDisruptionBudgets; BestEffort and Burstable over requests", 24, False),
        ("are preferred OOM victims via oom_score_adj", 24, False)
    ]
}

all_pass = True
for name, lines in cards.items():
    max_w = 1400 if name == "Footer" else card_text_w
    print(f"=== {name} (budget {max_w}px) ===")
    full_reconstructed = " ".join([l[0] for l in lines])
    for text, fs, mono in lines:
        w = measure(text, fs, mono)
        ok = w <= max_w
        if not ok:
            all_pass = False
        print(f"  [{'OK' if ok else 'FAIL'}] {w:5.1f}px (len {len(text):2d}) '{text}'")

print(f"\nAll pass: {all_pass}")
