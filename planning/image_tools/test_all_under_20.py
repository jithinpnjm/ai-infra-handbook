b2_refined2 = [
    "CRI plugin builds",
    "the OCI runtime spec",
    "config.json (args,",
    "env, cwd, user;",
    "mounts rootfs",
    "overlay, /proc,",
    "/sys, /dev, /dev/shm,",
    "volume binds,",
    "/etc/hosts,",
    "/etc/resolv.conf,",
    "termination log;",
    "joins sandbox net,",
    "IPC and UTS",
    "namespaces, own",
    "mnt and PID;",
    "cgroup under the",
    "pod cgroup;",
    "capabilities,",
    "seccomp, AppArmor,",
    "SELinux; devices)"
]

exp2 = "Create: CRI plugin builds the OCI runtime spec config.json (args, env, cwd, user; mounts rootfs overlay, /proc, /sys, /dev, /dev/shm, volume binds, /etc/hosts, /etc/resolv.conf, termination log; joins sandbox net, IPC and UTS namespaces, own mnt and PID; cgroup under the pod cgroup; capabilities, seccomp, AppArmor, SELinux; devices)"

assert " ".join(["Create:"] + b2_refined2) == exp2

max_w = 0
for i, l in enumerate(b2_refined2):
    w = len(l) * 14.4
    if w > max_w:
        max_w = w
    print(f"{i+1:2d}: [{len(l):2d} chars, {w:5.1f}px] {l}")
print(f"Max width: {max_w:.1f}px (Box width 356px leaves {(356-max_w)/2:.1f}px padding on each side)")
