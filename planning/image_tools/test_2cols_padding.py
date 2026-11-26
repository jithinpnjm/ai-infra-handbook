bw = 720

stages = [
    ("Stage 1", "Created to Scheduled", [
        ("creationTimestamp versus PodScheduled", 24, False),
        ("lastTransitionTime, scheduler metrics", 24, False)
    ]),
    ("Stage 2", "Scheduled to Initialized", [
        ("init containers, volume mounts, sandbox;", 24, False),
        ("Initialized condition", 24, False)
    ]),
    ("Stage 3", "Sandbox", [
        ("kubelet_run_podsandbox_duration_seconds", 24, True)
    ]),
    ("Stage 4", "Pull", [
        ("event Pulled in X, containerd logs", 24, False),
        ("kubelet_image_pull_duration_seconds", 24, True)
    ]),
    ("Stage 5", "Container start", [
        ("ContainersReady time", 24, False)
    ]),
    ("Stage 6", "Ready", [
        ("readiness probe success, Ready condition", 24, False)
    ]),
    ("Warm Node", "Warm node", [
        ("API and scheduling tens of ms, sandbox and CNI 100 to 500 ms, container under 1 s", 24, False)
    ]),
    ("Cold Node", "Cold node", [
        ("pull and unpack minutes, PVC attach 5 to 60 s, model load minutes", 24, False)
    ]),
    ("Bracket 1", "Overlay 1", [
        ("kubelet_pod_start_duration_seconds: from kubelet first seeing the pod until all regular containers run, includes image pull", 24, False)
    ]),
    ("Bracket 2", "Overlay 2", [
        ("kubelet_pod_start_sli_duration_seconds: SIG-Scalability SLI, excludes image pull and init container runtime", 24, False)
    ])
]

print("=== CHECKING 2-COLUMN / 720px PADDINGS ===")
for name, title, lines in stages:
    print(f"\n{name}:")
    for txt, fs, is_mono in lines:
        factor = 0.62 if is_mono else 0.60
        tw = len(txt) * fs * factor
        pad = (bw - tw) / 2
        print(f"  [{'OK' if pad >= 16 else 'FAIL'}] '{txt}' tw={tw:.1f}px, pad={pad:.1f}px (fs={fs})")
