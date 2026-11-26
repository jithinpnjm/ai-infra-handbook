import re
import xml.etree.ElementTree as ET

# Required labels:
labels = {
    "title": "Where each startup interval comes from",
    "seg1_title": "Created to Scheduled",
    "seg1_src": "creationTimestamp versus PodScheduled lastTransitionTime, scheduler metrics",
    "seg2_title": "Scheduled to Initialized",
    "seg2_src": "init containers, volume mounts, sandbox; Initialized condition",
    "seg3_title": "Sandbox",
    "seg3_src": "kubelet_run_podsandbox_duration_seconds",
    "seg4_title": "Pull",
    "seg4_src": "event Pulled in X, kubelet_image_pull_duration_seconds, containerd logs",
    "seg5_title": "Container start",
    "seg5_src": "ContainersReady time",
    "seg6_title": "Ready",
    "seg6_src": "readiness probe success, Ready condition",
    "bracket1": "kubelet_pod_start_duration_seconds: from kubelet first seeing the pod until all regular containers run, includes image pull",
    "bracket2": "kubelet_pod_start_sli_duration_seconds: SIG-Scalability SLI, excludes image pull and init container runtime",
    "warm": "API and scheduling tens of ms, sandbox and CNI 100 to 500 ms, container under 1 s",
    "cold": "pull and unpack minutes, PVC attach 5 to 60 s, model load minutes"
}

# Test wrapping for each
# Col widths:
# Total available = 1520 (x=40..1560)
# Let gaps = 16px (5 gaps = 80px)
# Width remaining = 1440.
# Let's allocate:
# col1: 250
# col2: 240
# col3: 270
# col4: 270
# col5: 200
# col6: 210
# Sum = 250+240+270+270+200+210 = 1440. Exactly 1440!

cols = [
    ("col1", 250, [
        # title
        ("Created to", 30, False),
        ("Scheduled", 30, False),
    ], [
        # source
        ("creationTimestamp", 24, False),
        ("versus", 24, False),
        ("PodScheduled", 24, False),
        ("lastTransition", 24, False),
        ("Time,", 24, False),
        ("scheduler metrics", 24, False)
    ]),
    ("col2", 240, [
        ("Scheduled to", 30, False),
        ("Initialized", 30, False),
    ], [
        ("init containers,", 24, False),
        ("volume mounts,", 24, False),
        ("sandbox;", 24, False),
        ("Initialized", 24, False),
        ("condition", 24, False)
    ]),
    ("col3", 270, [
        ("Sandbox", 30, False),
    ], [
        ("kubelet_run_", 24, True),
        ("podsandbox_", 24, True),
        ("duration_seconds", 24, True)
    ]),
    ("col4", 270, [
        ("Pull", 30, False),
    ], [
        ("event Pulled in X,", 24, False),
        ("kubelet_image_", 24, True),
        ("pull_duration_", 24, True),
        ("seconds, containerd", 24, False),
        ("logs", 24, False)
    ]),
    ("col5", 200, [
        ("Container", 30, False),
        ("start", 30, False),
    ], [
        ("Containers", 24, False),
        ("Ready time", 24, False)
    ]),
    ("col6", 210, [
        ("Ready", 30, False),
    ], [
        ("readiness probe", 24, False),
        ("success, Ready", 24, False),
        ("condition", 24, False)
    ])
]

print("=== CHECKING PADDINGS IN 6 COLUMNS ===")
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
