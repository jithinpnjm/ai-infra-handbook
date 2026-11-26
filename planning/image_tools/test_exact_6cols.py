# Check widths and paddings for all 6 columns:
cols = [
    ("Col 1 (Created to Scheduled)", 310, [
        ("Created to", 30, False),
        ("Scheduled", 30, False),
    ], [
        ("creationTimestamp", 24, False),
        ("versus", 24, False),
        ("PodScheduled", 24, False),
        ("lastTransitionTime,", 24, False),
        ("scheduler metrics", 24, False),
    ]),
    ("Col 2 (Scheduled to Initialized)", 240, [
        ("Scheduled to", 30, False),
        ("Initialized", 30, False),
    ], [
        ("init", 24, False),
        ("containers,", 24, False),
        ("volume", 24, False),
        ("mounts,", 24, False),
        ("sandbox;", 24, False),
        ("Initialized", 24, False),
        ("condition", 24, False),
    ]),
    ("Col 3 (Sandbox)", 265, [
        ("Sandbox", 30, False),
    ], [
        ("kubelet_run_", 24, True),
        ("podsandbox_", 24, True),
        ("duration_", 24, True),
        ("seconds", 24, True),
    ]),
    ("Col 4 (Pull)", 285, [
        ("Pull", 30, False),
    ], [
        ("event Pulled in X,", 24, False),
        ("kubelet_image_", 24, True),
        ("pull_duration_", 24, True),
        ("seconds,", 24, True),
        ("containerd logs", 24, False),
    ]),
    ("Col 5 (Container start)", 200, [
        ("Container", 30, False),
        ("start", 30, False),
    ], [
        ("Containers", 24, False),
        ("Ready time", 24, False),
    ]),
    ("Col 6 (Ready)", 220, [
        ("Ready", 30, False),
    ], [
        ("readiness", 24, False),
        ("probe success,", 24, False),
        ("Ready", 24, False),
        ("condition", 24, False),
    ]),
]

print("=== CHECKING 6-COLUMN PADDINGS WITH PROPORTIONAL WIDTHS ===")
all_pass = True
for name, bw, t_lines, s_lines in cols:
    print(f"\n{name} (width={bw}):")
    for txt, fs, is_mono in t_lines + s_lines:
        factor = 0.62 if is_mono else 0.60
        tw = len(txt) * fs * factor
        pad = (bw - tw) / 2
        ok = pad >= 16.0
        if not ok: all_pass = False
        print(f"  [{'OK' if ok else 'FAIL'}] '{txt}' tw={tw:.1f}px, pad={pad:.1f}px (fs={fs})")

print(f"\nAll padding >= 16px? {all_pass}")
