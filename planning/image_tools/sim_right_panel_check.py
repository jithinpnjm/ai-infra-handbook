from sim_layout import check_wrap

modes = [
    ("mode_bridge", "bridge: private subnet, veth per container, NAT outbound, -p publishes via DNAT; user-defined bridges add DNS-based name resolution and isolation"),
    ("mode_host", "host: shares the host namespace, no isolation, no NAT, best performance, ports conflict with host: NCCL or HPC containers"),
    ("mode_none", "none: only loopback"),
    ("mode_container", "container:NAME: shares another container's namespace (how a Kubernetes pod works)"),
    ("mode_overlay", "overlay: VXLAN across Docker hosts (Swarm)"),
    ("mode_macvlan", "macvlan or ipvlan: container on the physical network")
]

max_w = 492
total_lines = 0
for name, text in modes:
    lines = check_wrap(text, max_w, size=24)
    print(f"{name} ({len(lines)} lines):")
    for l in lines:
        w = len(l) * 24 * 0.6
        print(f"  [{len(l):2d} ch, {w:5.1f}px] {l}")
    total_lines += len(lines)
print(f"Total lines: {total_lines}")
