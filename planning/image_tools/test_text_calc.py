items = [
    ("Sources", ["Pod sources"], [32], ['sans']),
    ("API", ["API server", "(watch pods with", "spec.nodeName=this node)"], [30, 24, 24], ['sans', 'sans', 'mono']),
    ("FILE", ["Static pod", "manifests dir"], [30, 26], ['sans', 'sans']),
    ("HTTP", ["HTTP manifest URL", "(rare)"], [30, 24], ['sans', 'sans']),
    ("PM", ["Pod manager", "/ config merge"], [30, 26], ['sans', 'sans']),
    ("PW", ["Per-pod workers", "(syncPod)"], [32, 26], ['sans', 'mono']),
    ("VM", ["Volume manager", "(CSI, emptyDir, configmap...)"], [30, 24], ['sans', 'sans']),
    ("DM", ["Resource managers", "CPU / memory /", "topology / device"], [30, 24, 24], ['sans', 'sans', 'sans']),
    ("CRI", ["CRI client →", "containerd/CRI-O"], [30, 26], ['sans', 'mono']),
    ("PR", ["Prober", "(startup/readiness/liveness)"], [30, 24], ['sans', 'sans']),
    ("PLEG", ["PLEG: relist", "container states → events"], [30, 24], ['sans', 'sans']),
    ("SM", ["Status manager", "→ API server"], [30, 26], ['sans', 'sans']),
    ("EV", ["Eviction manager", "(node pressure)"], [30, 24], ['sans', 'sans']),
    ("IMG", ["Image GC /", "container GC"], [30, 28], ['sans', 'sans']),
    ("CAD", ["cAdvisor/cgroup stats", "→ /metrics, /stats/summary"], [30, 24], ['sans', 'mono']),
    ("LEASE", ["Node lease +", "node status heartbeats"], [30, 24], ['sans', 'sans']),
    ("KAPI", ["Kubelet HTTPS server :10250", "(logs, exec, attach,", "port-forward, metrics, pods)"], [30, 24, 24], ['sans', 'sans', 'sans']),
]

for name, lines, fss, fts in items:
    max_w = 0
    for l, fs, ft in zip(lines, fss, fts):
        coeff = 0.62 if ft == 'mono' else 0.60
        w = len(l) * coeff * fs
        if w > max_w: max_w = w
    print(f"{name:8s}: max_w = {max_w:5.1f} px, needed box_w (with 32 pad + 72 icon beside) = {max_w + 104:5.1f} px, (with icon above) = {max_w + 40:5.1f} px")
