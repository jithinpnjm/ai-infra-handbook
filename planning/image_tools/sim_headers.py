# Check text lines and required widths
labels = [
    ("kubectl", ["kubectl"]),
    ("kube-apiserver", ["kube-", "apiserver"]),
    ("etcd", ["etcd"]),
    ("controller-manager", ["controller-", "manager"]),
    ("scheduler", ["scheduler"]),
    ("kubelet (node)", ["kubelet", "(node)"]),
    ("runtime (containerd)", ["runtime", "(containerd)"]),
]

for name, lines in labels:
    print(f"{name}:")
    for l in lines:
        w30 = len(l) * 0.6 * 30
        w24 = len(l) * 0.6 * 24
        print(f"  '{l}': at 30px = {w30:.1f}px (box min {w30+32:.1f}), at 24px = {w24:.1f}px (box min {w24+32:.1f})")
