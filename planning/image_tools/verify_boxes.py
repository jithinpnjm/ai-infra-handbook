import math

boxes = [
    {
        "id": "LEASE",
        "w": 340, "h": 150,
        "lines": [
            ("Node lease +", 30, "sans", True),
            ("node status heartbeats", 24, "sans", False)
        ]
    },
    {
        "id": "Sources",
        "w": 1160, "h": 175,
        "lines": [
            ("Pod sources", 30, "sans", True)
        ]
    },
    {
        "id": "API",
        "w": 400, "h": 120,
        "lines": [
            ("API server", 30, "sans", True),
            ("(watch pods with", 24, "sans", False),
            ("spec.nodeName=this node)", 24, "mono", False)
        ]
    },
    {
        "id": "FILE",
        "w": 340, "h": 120,
        "lines": [
            ("Static pod", 30, "sans", True),
            ("manifests dir", 26, "sans", False)
        ]
    },
    {
        "id": "HTTP",
        "w": 360, "h": 120,
        "lines": [
            ("HTTP manifest URL", 30, "sans", True),
            ("(rare)", 24, "sans", False)
        ]
    },
    {
        "id": "CAD",
        "w": 440, "h": 125,
        "lines": [
            ("cAdvisor/cgroup stats", 30, "sans", True),
            ("→ /metrics, /stats/summary", 24, "mono", False)
        ]
    },
    {
        "id": "PM",
        "w": 440, "h": 115,
        "lines": [
            ("Pod manager", 30, "sans", True),
            ("/ config merge", 26, "sans", False)
        ]
    },
    {
        "id": "IMG",
        "w": 440, "h": 115,
        "lines": [
            ("Image GC / container GC", 30, "sans", True)
        ]
    },
    {
        "id": "EV",
        "w": 440, "h": 115,
        "lines": [
            ("Eviction manager", 30, "sans", True),
            ("(node pressure)", 24, "sans", False)
        ]
    },
    {
        "id": "PW",
        "w": 480, "h": 130,
        "lines": [
            ("Per-pod workers", 32, "sans", True),
            ("(syncPod)", 26, "mono", False)
        ]
    },
    {
        "id": "CRI",
        "w": 440, "h": 115,
        "lines": [
            ("CRI client →", 30, "sans", True),
            ("containerd/CRI-O", 26, "mono", False)
        ]
    },
    {
        "id": "VM",
        "w": 440, "h": 125,
        "lines": [
            ("Volume manager", 30, "sans", True),
            ("(CSI, emptyDir, configmap...)", 24, "sans", False)
        ]
    },
    {
        "id": "PLEG",
        "w": 440, "h": 120,
        "lines": [
            ("PLEG: relist container", 30, "sans", True),
            ("states → events", 26, "sans", False)
        ]
    },
    {
        "id": "DM",
        "w": 440, "h": 130,
        "lines": [
            ("Resource managers", 30, "sans", True),
            ("CPU / memory /", 24, "sans", False),
            ("topology / device", 24, "sans", False)
        ]
    },
    {
        "id": "PR",
        "w": 440, "h": 125,
        "lines": [
            ("Prober", 30, "sans", True),
            ("(startup/readiness/liveness)", 24, "sans", False)
        ]
    },
    {
        "id": "SM",
        "w": 440, "h": 120,
        "lines": [
            ("Status manager", 30, "sans", True),
            ("→ API server", 26, "sans", False)
        ]
    },
    {
        "id": "KAPI",
        "w": 1100, "h": 140,
        "lines": [
            ("Kubelet HTTPS server :10250", 30, "sans", True),
            ("(logs, exec, attach, port-forward, metrics, pods)", 24, "sans", False)
        ]
    }
]

all_ok = True
for b in boxes:
    bw, bh = b["w"], b["h"]
    for text, fs, font_type, is_bold in b["lines"]:
        coeff = 0.62 if font_type == "mono" else 0.60
        tw = len(text) * coeff * fs
        pad = (bw - tw) / 2
        if pad < 16:
            print(f"FAILED padding for {b['id']}: line '{text}' tw={tw:.1f}, bw={bw}, pad={pad:.1f} < 16!")
            all_ok = False
        if fs < 24:
            print(f"FAILED font size for {b['id']}: {fs} < 24!")
            all_ok = False

if all_ok:
    print("ALL TEXT LINES FIT WITH AT LEAST 16 PX PADDING AND NO FONT < 24 PX!")
