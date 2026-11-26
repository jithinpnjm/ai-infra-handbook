import re

# Col width = 470px
# 3 cols: 40 + 470 + 45 + 470 + 45 + 470 + 40 = 1580px (Margins = 50px each side!)
bw = 470

stages = [
    ("Stage 1", "Created to Scheduled", [
        ("creationTimestamp versus", 24, False),
        ("PodScheduled", 24, False),
        ("lastTransitionTime,", 24, False),
        ("scheduler metrics", 24, False)
    ]),
    ("Stage 2", "Scheduled to Initialized", [
        ("init containers, volume mounts,", 24, False),
        ("sandbox; Initialized condition", 24, False)
    ]),
    ("Stage 3", "Sandbox", [
        ("kubelet_run_podsandbox_", 24, True),
        ("duration_seconds", 24, True)
    ]),
    ("Stage 4", "Pull", [
        ("event Pulled in X,", 24, False),
        ("kubelet_image_pull_duration_seconds,", 24, True),
        ("containerd logs", 24, False)
    ]),
    ("Stage 5", "Container start", [
        ("ContainersReady time", 24, False)
    ]),
    ("Stage 6", "Ready", [
        ("readiness probe success,", 24, False),
        ("Ready condition", 24, False)
    ])
]

print("=== CHECKING 3-COLUMN LAYOUT (bw=470px) ===")
all_pass = True
for stage_name, title, lines in stages:
    print(f"\n{stage_name}: {title}")
    # title check
    tw_title = len(title) * 30 * 0.60
    pad_title = (bw - tw_title) / 2
    print(f"  Title: '{title}' tw={tw_title:.1f}px, pad={pad_title:.1f}px")
    if pad_title < 16.0: all_pass = False
    for txt, fs, is_mono in lines:
        factor = 0.62 if is_mono else 0.60
        tw = len(txt) * fs * factor
        pad = (bw - tw) / 2
        ok = pad >= 16.0
        if not ok: all_pass = False
        print(f"  [{'OK' if ok else 'FAIL'}] '{txt}' tw={tw:.1f}px, pad={pad:.1f}px")

print(f"\nAll padding >= 16px? {all_pass}")
