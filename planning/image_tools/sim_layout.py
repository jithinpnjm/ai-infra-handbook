import sys

def check_wrap(text, max_w, size=24, mono=False):
    rate = 0.62 if mono else 0.6
    words = text.split(" ")
    lines = []
    curr = []
    for w in words:
        test = " ".join(curr + [w])
        if len(test) * size * rate <= max_w:
            curr.append(w)
        else:
            if curr:
                lines.append(" ".join(curr))
                curr = [w]
            else:
                lines.append(w)
                curr = []
    if curr:
        lines.append(" ".join(curr))
    return lines

# Let's test Docker network modes in right panel:
# Width of right panel: say 560px, inner max_w = 560 - 48 = 512px
modes = [
    "bridge: private subnet, veth per container, NAT outbound, -p publishes via DNAT; user-defined bridges add DNS-based name resolution and isolation",
    "host: shares the host namespace, no isolation, no NAT, best performance, ports conflict with host: NCCL or HPC containers",
    "none: only loopback",
    "container:NAME: shares another container's namespace (how a Kubernetes pod works)",
    "overlay: VXLAN across Docker hosts (Swarm)",
    "macvlan or ipvlan: container on the physical network"
]

print("--- RIGHT PANEL WRAPPING (w=512) ---")
total_lines = 0
for m in modes:
    lines = check_wrap(m, 512, size=24)
    print(f"Item ({len(lines)} lines):")
    for l in lines:
        print("  ", l)
    total_lines += len(lines)
print(f"Total lines in right panel: {total_lines}")
