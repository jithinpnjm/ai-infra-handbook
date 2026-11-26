messages = [
    # 1: U -> A
    ("U", "A", "POST/PATCH Deployment"),
    # 2: A -> A
    ("A", "A", "authn, authz, admission (mutate/validate)"),
    # 3: A -> E
    ("A", "E", "persist Deployment"),
    # 4: CM -> A
    ("CM", "A", "(watch) Deployment created"),
    # 5: CM -> A
    ("CM", "A", "create ReplicaSet (deployment controller)"),
    # 6: CM -> A
    ("CM", "A", "(watch) ReplicaSet \u2192 create Pods (replicaset controller)"),
    # 7: S -> A
    ("S", "A", "(watch) Pod with no nodeName"),
    # 8: S -> S
    ("S", "S", "filter + score nodes"),
    # 9: S -> A
    ("S", "A", "bind: set spec.nodeName"),
    # 10: K -> A
    ("K", "A", "(watch) Pod bound to me"),
    # 11: K -> R
    ("K", "R", "CRI: RunPodSandbox, CreateContainer, StartContainer (CNI, CSI mounts)"),
    # 12: K -> A
    ("K", "A", "update Pod status (Running, IPs, conditions)"),
    # 13: CM -> A
    ("CM", "A", "EndpointSlice controller adds the Pod IP when Ready")
]

for i, (src, dst, text) in enumerate(messages, 1):
    w_sans = len(text) * 0.6 * 24
    w_mono = len(text) * 0.62 * 24
    print(f"Step {i:2d} ({src}->{dst}): len={len(text):2d}, w_sans={w_sans:.1f}px, w_mono={w_mono:.1f}px : '{text}'")
