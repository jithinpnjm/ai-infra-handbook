import re

items = [
    # Col 1: Pod / Runtime level
    ("What does the runtime think exists: crictl pods, crictl ps -a, crictl inspectp, crictl inspect (pid, exit code, mounts, resources), crictl logs, crictl stats; ctr -n k8s.io tasks ls"),
    ("What do the kubelet and runtime say: journalctl -u kubelet -u containerd --since -30 min"),
    ("Which namespaces does this process live in: lsns -p PID, ls -l /proc/PID/ns, /proc/PID/cgroup; get PID with crictl inspect template info.pid"),
    ("What is the pod network doing: nsenter -t PID -n ip addr, ip route, ss -tnap, tcpdump"),
    ("What does the pod filesystem look like: nsenter -t PID -m ls, cat /proc/mounts, df -h"),
    # Col 2: Node / Kernel / HW level
    ("Kernel network counters: ip -s link, nstat, conntrack -S, ethtool -S, iptables-save, nft list ruleset, ipvsadm -Ln"),
    ("Storage: findmnt, lsblk, df -hT, df -i, iostat -x, fio"),
    ("CPU, memory, I/O of the process: top -H, pidstat, perf, strace, py-spy, gdb"),
    ("GPU and fabric: nvidia-smi, dcgmi, journalctl -k grep Xid, lspci -vv, ibstat, all_reduce_perf"),
]

for i, item in enumerate(items, 1):
    parts = item.split(": ", 1)
    q = parts[0] + ":"
    c = parts[1]
    print(f"Item {i}:")
    print(f"  Question: '{q}' (len={len(q)}, width~{len(q)*30*0.6:.1f}px)")
    print(f"  Commands: '{c}' (len={len(c)}, width~{len(c)*24*0.62:.1f}px)")
