b2_lines = [
    "CRI plugin builds the",
    "OCI runtime spec",
    "config.json (args, env,",
    "cwd, user; mounts",
    "rootfs overlay,",
    "/proc, /sys, /dev,",
    "/dev/shm, volume binds,",
    "/etc/hosts,",
    "/etc/resolv.conf,",
    "termination log; joins",
    "sandbox net, IPC and",
    "UTS namespaces,",
    "own mnt and PID;",
    "cgroup under the",
    "pod cgroup;",
    "capabilities, seccomp,",
    "AppArmor, SELinux;",
    "devices)"
]
# wait, config.json (args, env, is 23 chars. Can we do:
# config.json
# (args, env, cwd, user;
# mounts rootfs overlay,
# /proc, /sys, /dev,
# /dev/shm, volume binds,

b2_refined = [
    "CRI plugin builds",
    "the OCI runtime spec",
    "config.json (args,",
    "env, cwd, user; mounts",
    "rootfs overlay,",
    "/proc, /sys, /dev,",
    "/dev/shm,",
    "volume binds,",
    "/etc/hosts,",
    "/etc/resolv.conf,",
    "termination log;",
    "joins sandbox net,",
    "IPC and UTS",
    "namespaces, own",
    "mnt and PID; cgroup",
    "under the pod cgroup;",
    "capabilities,",
    "seccomp, AppArmor,",
    "SELinux; devices)"
]

exp2 = "Create: CRI plugin builds the OCI runtime spec config.json (args, env, cwd, user; mounts rootfs overlay, /proc, /sys, /dev, /dev/shm, volume binds, /etc/hosts, /etc/resolv.conf, termination log; joins sandbox net, IPC and UTS namespaces, own mnt and PID; cgroup under the pod cgroup; capabilities, seccomp, AppArmor, SELinux; devices)"

assert " ".join(["Create:"] + b2_refined) == exp2

for i, l in enumerate(b2_refined):
    w = len(l) * 14.4
    print(f"{i+1:2d}: [{len(l):2d} chars, {w:5.1f}px] {l}")
