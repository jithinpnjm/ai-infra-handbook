from sim_layout import check_wrap

modes = [
    ("mode_bridge", "bridge: private subnet, veth per container, NAT outbound, -p publishes via DNAT; user-defined bridges add DNS-based name resolution and isolation"),
    ("mode_host", "host: shares the host namespace, no isolation, no NAT, best performance, ports conflict with host: NCCL or HPC containers"),
    ("mode_none", "none: only loopback"),
    ("mode_container", "container:NAME: shares another container's namespace (how a Kubernetes pod works)"),
    ("mode_overlay", "overlay: VXLAN across Docker hosts (Swarm)"),
    ("mode_macvlan", "macvlan or ipvlan: container on the physical network")
]

max_w = 532 # 580 - 48
all_lines = []
for name, text in modes:
    lines = check_wrap(text, max_w, size=24)
    print(f"{name}:")
    for l in lines:
        w = len(l) * 24 * 0.6
        print(f"   ({len(l):2d} ch, {w:5.1f}px / {max_w}px) : {l}")
        all_lines.append(l)

print(f"\nTotal lines: {len(all_lines)}")
