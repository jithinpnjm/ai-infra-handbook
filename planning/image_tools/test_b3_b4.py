b3_lines = [
    "containerd launches",
    "the shim, shim calls",
    "runc create",
    "(namespaces,",
    "pivot_root, cgroups,",
    "drop capabilities,",
    "install seccomp),",
    "then runc start",
    "execs the entrypoint",
    "as PID 1, child",
    "of the shim"
]

exp3 = "Start: containerd launches the shim, shim calls runc create (namespaces, pivot_root, cgroups, drop capabilities, install seccomp), then runc start execs the entrypoint as PID 1, child of the shim"
assert " ".join(["Start:"] + b3_lines) == exp3

max_w3 = max(len(l) * 14.4 for l in b3_lines)
print(f"B3 Max width: {max_w3:.1f}px (padding {(356-max_w3)/2:.1f}px)")

b4_lines = [
    "post-start hook,",
    "startup, readiness,",
    "liveness; exec probes",
    "via CRI ExecSync",
    "inside the container;",
    "HTTP, TCP, gRPC probes",
    "from the node to",
    "the pod IP; readiness",
    "change updates Ready",
    "then EndpointSlice",
    "controller adds or",
    "removes the IP"
]
# in b4: "HTTP, TCP, gRPC probes" = 22 chars = 316.8px
# can split:
b4_refined = [
    "post-start hook,",
    "startup, readiness,",
    "liveness; exec",
    "probes via CRI",
    "ExecSync inside",
    "the container;",
    "HTTP, TCP, gRPC",
    "probes from the",
    "node to the pod IP;",
    "readiness change",
    "updates Ready then",
    "EndpointSlice",
    "controller adds or",
    "removes the IP"
]

exp4 = "Probes: post-start hook, startup, readiness, liveness; exec probes via CRI ExecSync inside the container; HTTP, TCP, gRPC probes from the node to the pod IP; readiness change updates Ready then EndpointSlice controller adds or removes the IP"
assert " ".join(["Probes:"] + b4_refined) == exp4

for i, l in enumerate(b4_refined):
    print(f"{i+1:2d}: [{len(l):2d} chars, {len(l)*14.4:5.1f}px] {l}")

max_w4 = max(len(l) * 14.4 for l in b4_refined)
print(f"B4 Max width: {max_w4:.1f}px (padding {(356-max_w4)/2:.1f}px)")
