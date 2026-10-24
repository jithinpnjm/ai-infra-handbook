---
id: "c05-26"
title: "5.26 How Kubernetes uses the Linux kernel: a complete map"
sidebar_label: "5.26 How Kubernetes uses the Linux kernel: a complete map"
sidebar_position: 26
description: "A synthesis of every Linux kernel facility Kubernetes depends on: namespaces, cgroups v2, capabilities, seccomp and LSMs, overlayfs and mounts, netfilter/conntrack/eBPF/tc, virtual devices, the CPU scheduler, memory management (OOM, hugepages, NUMA, swap), block and filesystem layers, devices (GPU, RDMA), time, entropy, and the kernel parameters, versions and failure modes that matter"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.26 How Kubernetes uses the Linux kernel: a complete map

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | Linux VM/bare metal with root and a kubeadm/kind cluster; `lsns`, `systemd-cgls`, `bpftool`, `perf`, `strace`, `sysctl` |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Kubernetes does not isolate, schedule or limit anything by itself: it asks the Linux kernel to do it. Every behaviour you will debug on a GPU node (a container killed with exit 137, a pod that sees only some GPUs, a throttled data loader, pods unable to connect after a rule update, memory that "disappears", an RDMA NIC unusable inside a pod, a kernel upgrade that breaks the GPU driver) is a kernel mechanism surfacing through a Kubernetes API. This chapter is the map from Kubernetes concepts to kernel features, with the kernel parameters, versions, and failure modes that matter for GPU hosts. It consolidates Parts 1 and 2 (Linux and networking) with Part 5.

## Prerequisites and outcomes

Needs Parts 1 and 2 and 5.1 to 5.15. After this chapter you can:

- For any Kubernetes feature, name the kernel mechanism(s) behind it and where to inspect them (`/proc`, `/sys`, tools).
- Explain precisely what a container is at the kernel level (a process with namespaces, cgroup membership, capability set, seccomp filter, LSM label, mount namespace with a rootfs) and which features require which kernel versions.
- Reason about resource enforcement (CPU CFS quota/weight, memory max/high/OOM, pids, I/O, hugetlb) and its observable failure modes.
- Understand how networking features (veth, bridges, VXLAN, netfilter, conntrack, eBPF, tc, XDP) implement CNI and Services.
- Understand storage mechanics (overlayfs, bind mounts, mount propagation, block devices, FUSE, NFS clients, page cache) and device access (cgroup device controller, GPU/RDMA devices).
- Choose and tune kernel versions, boot parameters, and sysctls for GPU Kubernetes nodes; diagnose kernel-level issues.

## 1. The master map

```mermaid
flowchart TB
  subgraph K8s["Kubernetes concept"]
    P["Pod / container"]
    R["Resources (requests/limits, QoS)"]
    N["Pod network, Service, NetworkPolicy"]
    V["Volumes, images, logs"]
    D["Devices (GPU, RDMA)"]
    S["Security context, PSS, runtime class"]
    SC["Scheduling hints (CPU/NUMA managers)"]
  end
  subgraph Kernel["Linux kernel feature"]
    NS["Namespaces: pid, mnt, net, uts, ipc, user, cgroup, time"]
    CG["cgroups v2: cpu, memory, io, pids, hugetlb, cpuset, devices (BPF), rdma"]
    CAP["Capabilities, no_new_privs, seccomp-bpf, LSM (AppArmor/SELinux), user namespaces"]
    FS["overlayfs, bind mounts, mount propagation, tmpfs, FUSE, page cache, block layer"]
    NET["veth, bridge, VXLAN/Geneve, routing, netfilter/nftables, conntrack, tc, eBPF/XDP"]
    DEV["Device nodes, devtmpfs/udev, PCI, VFIO, SR-IOV, RDMA verbs, IOMMU"]
    SCHED["CFS/EEVDF scheduler, cpusets, NUMA, hugepages, OOM killer, PSI"]
  end
  P --> NS & CG & CAP & FS
  R --> CG & SCHED
  N --> NET & NS
  V --> FS
  D --> DEV & CG
  S --> CAP & NS
  SC --> SCHED & DEV
```

| Kubernetes feature | Kernel mechanism | Inspect with |
|---|---|---|
| Pod isolation (PID, mount, UTS, IPC, network) | Namespaces (`clone`/`unshare`/`setns`) | `lsns`, `/proc/PID/ns/*`, `nsenter` |
| Pod network namespace shared by containers | A single netns joined by all containers' setns | `ip netns`, `/proc/PID/ns/net` inode comparison |
| User namespaces for pods (`hostUsers: false`) | `CLONE_NEWUSER` + idmapped mounts | `/proc/PID/uid_map`, kernel ≥ 6.3 for idmapped overlay |
| CPU limit | CFS bandwidth control (`cpu.max`) | `cpu.stat` (`nr_throttled`, `throttled_usec`) |
| CPU request | CPU weight (`cpu.weight`, formerly shares) | `cpu.weight` |
| Exclusive CPUs (static CPU manager) | cpusets (`cpuset.cpus`) | `cpuset.cpus.effective`, `taskset -pc` |
| Memory limit / OOM | memory controller (`memory.max`, `memory.high`, `memory.min`), OOM killer, `oom_score_adj` | `memory.events`, `dmesg`, `/proc/PID/oom_score*` |
| Ephemeral storage limit / eviction | kubelet accounting of filesystem usage (du/inode counting, project quotas optional) | `df`, XFS quotas |
| PID limit (`podPidsLimit`) | pids controller (`pids.max`) | `pids.current`, `pids.events` |
| Block I/O limits (rare) | io controller (`io.max`, `io.weight`), blk-throttle | `io.stat`, `io.pressure` |
| Hugepages resources | hugetlb controller, hugetlbfs | `/sys/kernel/mm/hugepages`, `hugetlb.*` files |
| Image layers / writable layer | overlayfs (`lowerdir`, `upperdir`, `workdir`) | `mount \| grep overlay`, `/var/lib/containerd/.../snapshots` |
| Volumes into containers | bind mounts, mount propagation | `findmnt`, `/proc/PID/mountinfo` |
| Secrets/ConfigMaps/`emptyDir{Memory}` | tmpfs | `df -h`, `mount \| grep tmpfs` |
| `/dev/shm` | tmpfs mounted at `/dev/shm` | `df -h /dev/shm` |
| Device exposure (GPU, RDMA) | devtmpfs nodes + cgroup devices allowlist (BPF device filter) | `ls -l /dev/nvidia*`, `bpftool cgroup tree` |
| Capabilities, `allowPrivilegeEscalation` | capability sets, `PR_SET_NO_NEW_PRIVS` | `/proc/PID/status` (`CapEff`, `NoNewPrivs`), `capsh --decode` |
| `seccompProfile` | seccomp-bpf filters | `/proc/PID/status` (`Seccomp: 2`), `strace` EPERM |
| AppArmor/SELinux | LSMs | `aa-status`, `ps -Z`, `ausearch -m avc` |
| `hostNetwork` | Use the root network namespace | `ip addr` identical to host |
| veth/bridge/routes (CNI) | veth, bridge, FIB, ARP/neighbour | `ip link/route/neigh`, `bridge` |
| Overlay (VXLAN/Geneve/IPIP) | tunnel devices with UDP encap | `ip -d link`, `bridge fdb` |
| Services (kube-proxy) | netfilter NAT (iptables/nft), IPVS, or BPF maps; conntrack | `iptables-save`, `ipvsadm`, `conntrack`, `bpftool map` |
| NetworkPolicy | netfilter rules/ipsets or eBPF programs on tc/XDP | `iptables`, `bpftool prog`, `cilium bpf` |
| Bandwidth limits (annotation) | tc (HTB/TBF or EDT with fq) | `tc qdisc show`, `tc -s class show` |
| Load balancing node ports | netfilter/IPVS/BPF; `route_localnet` | sysctls |
| Probes (exec) | `setns` + `execve` inside container namespaces | n/a |
| Logs | pipes/pty to runtime, files on host | `/var/log/pods` |
| Time (`time` namespace, rarely) | CLOCK_MONOTONIC offsets | n/a |
| Node resource pressure signals | PSI (`/proc/pressure/*`), memory counters | `cat /proc/pressure/memory` |
| Pod QoS and eviction ordering | cgroup placement + `oom_score_adj` | cgroup tree |
| Container checkpoint/restore (alpha) | CRIU, ptrace, userfaultfd | `criu check` |
| User-space networking (DPDK/RDMA) | VFIO, hugepages, IOMMU, uverbs | `/dev/vfio`, `/dev/infiniband` |

## 2. Namespaces in depth

Eight namespace types (`man 7 namespaces`): **mnt** (mount table; `pivot_root` into the image rootfs), **pid** (PID numbering and signal visibility; PID 1 semantics), **net** (interfaces, routing tables, netfilter, sockets), **uts** (hostname), **ipc** (SysV IPC/POSIX message queues), **user** (UID/GID mapping, capabilities scoped to the namespace), **cgroup** (virtualised cgroup root), **time** (clock offsets). Creating: `clone(2)` flags, `unshare(2)`, `setns(2)`; persistence: a namespace lives while a process is in it, an open fd to `/proc/PID/ns/*`, or a bind mount of that file (`/var/run/netns/<name>`). A pod = containers sharing net/ipc/uts (+ optionally pid with `shareProcessNamespace`) namespaces created by the **pause** container; each container has its own mnt (and usually pid) namespace.

Key details:

- **PID namespace**: PID 1 ignores signals without handlers (SIGTERM won't kill an app that doesn't install a handler), reaps orphans (zombie reaping responsibility); `kill -9` from outside works only from an ancestor namespace. `shareProcessNamespace: true` lets containers see each other's processes (debug sidecars) but PID 1 is the pause container.
- **Network namespace**: sockets bound in a netns are invisible elsewhere; `localhost` is per-netns; `net.*` sysctls are mostly per-netns (`net.ipv4.ip_local_port_range`, `tcp_*` per-netns since newer kernels), others host-global (`nf_conntrack_max`, `net.core.somaxconn` is per-netns, `fs.*` global); pods may set "safe" namespaced sysctls via `securityContext.sysctls`.
- **Mount namespace**: copy of the parent's mounts at creation; propagation flags (`shared`, `slave`, `private`, `unbindable`) determine whether later mounts appear in other namespaces; kubelet/CSI use `Bidirectional` propagation for the node plugin.
- **User namespace**: maps container UID 0 to an unprivileged host UID range; capabilities in the child namespace don't apply to resources owned by the parent (e.g., mounting arbitrary filesystems); pod user namespaces (`hostUsers: false`) need kernel support for idmapped mounts on the volumes/overlay (≥ 5.12 for idmapped mounts; overlayfs idmapped ≥ 5.19; CRI support), greatly reducing the impact of container escapes.
- **IPC namespace**: POSIX shared memory (`/dev/shm` is tmpfs in the *mount* namespace; SysV IPC separate); `hostIPC: true` shares with host (used by some HPC/MPI shared memory setups; weakens isolation).
- **cgroup namespace**: container sees `/sys/fs/cgroup` rooted at its own cgroup.

## 3. cgroups v2 in depth

cgroup v2 is a single unified hierarchy (`/sys/fs/cgroup`) with controllers enabled per subtree through `cgroup.subtree_control`; processes live only in leaf cgroups ("no internal process" rule, except the root). Kubernetes (and systemd) create `kubepods.slice` → QoS slices → pod slices → container scopes (5.9). Controllers and the Kubernetes mapping:

| Controller | Files | Kubernetes use |
|---|---|---|
| **cpu** | `cpu.weight` (1–10000, default 100), `cpu.max` ("quota period", e.g., `200000 100000` = 2 CPUs), `cpu.stat`, `cpu.pressure`, `cpu.idle` | requests → weight, limits → max; throttling shows as `nr_throttled`/`throttled_usec`; burst (`cpu.max.burst`) |
| **memory** | `memory.max` (hard), `memory.high` (throttle/reclaim threshold), `memory.min`/`memory.low` (protection), `memory.swap.max`, `memory.current`, `memory.stat`, `memory.events` (`low, high, max, oom, oom_kill`), `memory.oom.group` | limit → `max`; MemoryQoS sets `high`/`min`; includes page cache, kernel memory (slab), tmpfs/shmem |
| **io** | `io.max`, `io.weight`, `io.latency`, `io.stat`, `io.pressure` | rarely set by Kubernetes; used by node tuning |
| **pids** | `pids.max`, `pids.current`, `pids.events` | `podPidsLimit` |
| **cpuset** | `cpuset.cpus`, `cpuset.mems`, `cpuset.cpus.effective` | static CPU manager exclusivity, memory manager NUMA pinning |
| **hugetlb** | `hugetlb.<size>.max/current` | hugepages-* resources |
| **rdma** | `rdma.max`, `rdma.current` | RDMA resource limits (rarely used by Kubernetes today) |
| **devices** | Implemented as cgroup BPF programs (`BPF_PROG_TYPE_CGROUP_DEVICE`) in v2 | Runtime attaches an allow-list program per container: only allocated `/dev/nvidia*` etc. |
| **misc** | `misc.max` | scalar resources |
| **freezer** | `cgroup.freeze` | pause/checkpoint |
| **PSI** | `cpu/memory/io.pressure` | node pressure signals, load-shedding |

Behaviours that explain incidents:

- **CPU throttling**: with `cpu.max` quota, a multi-threaded process using 8 threads on a 2-CPU limit burns its quota in the first 25 ms of each 100 ms period and stalls for 75 ms ("throttling") although average utilisation looks low; tail latency spikes, probe timeouts. Remedies: remove CPU limits (keep requests) for latency-sensitive pods, align thread counts with limits (`OMP_NUM_THREADS`, `GOMAXPROCS` via downward API/`automaxprocs`), use static CPU manager, newer kernels with burst or `cpu.idle`. Kernel CFS bandwidth bugs in old kernels (< 5.4) over-throttled; ensure current kernels.
- **Memory accounting**: `memory.current` includes anonymous pages, file cache (page cache), tmpfs, and kernel memory (page tables, slab, socket buffers). Page cache is reclaimable under `memory.max` pressure, but active tmpfs pages and pinned/mlock'd memory are not. OOM happens when reclaim fails: kernel kills a process in the cgroup (`memory.oom.group=1` kills the whole group, which Kubernetes enables for containers in newer versions). Metrics: `container_memory_working_set_bytes` (current − inactive_file) is what the kubelet uses for eviction decisions; compare to `memory.max`.
- **Swap**: disabled by default in Kubernetes; the NodeSwap feature (beta) permits limited swap for Burstable pods on cgroup v2 (`memory.swap.max`), not recommended for GPU/ML nodes.
- **Hierarchy limits**: a pod-level limit constrains the sum of containers; kubelet node allocatable sets `kubepods` max (5.9).
- **io/blk**: container log writes and image unpacks can saturate disks, impacting latency; use separate devices for container storage; apply io.weight on system vs pods where needed.
- **Accounting cost**: memory cgroup kernel-memory accounting and many cgroups (tens of thousands) slow `cat memory.stat`/cAdvisor scans and cause "cgroup leaks" (dead cgroups lingering until page cache drains); symptoms: high kernel CPU in `mem_cgroup_*`, growing number of `nr_dying_descendants` in `cgroup.stat`.

Hybrid vs unified: cgroup v1 is deprecated in Kubernetes (maintenance mode; some features require v2). Check `stat -fc %T /sys/fs/cgroup` → `cgroup2fs`; boot parameter `systemd.unified_cgroup_hierarchy=1`; RHEL 8+, Ubuntu 22.04+, Debian 11+ default to v2.

## 4. Security primitives

- **Capabilities** split root into ~40 privileges (CAP_NET_ADMIN, CAP_SYS_ADMIN, CAP_NET_RAW, CAP_IPC_LOCK, CAP_SYS_PTRACE...). Container default set (Docker/containerd): CHOWN, DAC_OVERRIDE, FSETID, FOWNER, MKNOD, NET_RAW, SETGID, SETUID, SETFCAP, SETPCAP, NET_BIND_SERVICE, SYS_CHROOT, KILL, AUDIT_WRITE. `drop: [ALL]` then add only what's needed. Sets: permitted, effective, inheritable, bounding, ambient. `CAP_SYS_ADMIN` is nearly root (avoid; DCGM exporter historically asks for it).
- **`no_new_privs`** (`allowPrivilegeEscalation: false`): blocks setuid/file capability elevation across `execve`.
- **seccomp-bpf**: syscall filter. RuntimeDefault profile blocks ~40 to 60 dangerous syscalls (`kexec_load`, `ptrace` variants, `mount`, `keyctl`, `bpf` etc.); `seccompDefault` in kubelet applies it to all; custom profiles (Localhost) tailored to apps; failure shows as `EPERM`/`Operation not permitted` or `SIGSYS`; debug with `strace`, audit logs, or the Security Profiles Operator recorder.
- **LSMs**: AppArmor (path-based; default `cri-containerd.apparmor.d`), SELinux (label-based; `container_t` type with MCS categories isolating containers); GPU device access under SELinux requires correct labels for `/dev/nvidia*` (`container_use_devices` boolean or custom policy via `nvidia-container-toolkit` SELinux support).
- **Landlock, IMA, kernel lockdown, Yama ptrace_scope, seccomp user notifications** are additional levers (`kernel.yama.ptrace_scope` affects debugging with `strace -p`).
- **User namespaces & rootless**: see above.
- **Kernel attack surface**: because containers share the host kernel, kernel CVEs (e.g., Dirty Pipe, overlayfs, netfilter nf_tables bugs) are container escapes; patch kernels promptly, reduce syscall surface (seccomp), restrict `CAP_SYS_ADMIN`/`CAP_NET_ADMIN`, disable unprivileged user namespaces if unused (`user.max_user_namespaces`, `kernel.unprivileged_userns_clone`) or confine them, use sandboxed runtimes for untrusted code (5.2).

## 5. Filesystems, mounts and block I/O

- **overlayfs**: union mount of read-only `lowerdir`s (image layers) with `upperdir` (container writable layer) and `workdir`; copy-up on first write (whole file; slow for huge files like checkpoints written inside the container filesystem), whiteouts for deletions, inode/`st_dev` quirks (hard links, `rename` across layers returning EXDEV), `d_type` support required (xfs needs `ftype=1`), `metacopy`/`redirect_dir` options, page cache sharing for identical lowers. Performance: metadata-heavy workloads (many small files) suffer vs a dedicated volume; keep datasets and checkpoints on volumes.
- **Bind mounts and propagation**: Kubernetes volumes are bind-mounted into containers; `mountPropagation` modes; `subPath` bind mounts.
- **tmpfs**: `emptyDir{medium: Memory}`, `/dev/shm`, Secret/ConfigMap volumes; charged to the container's memory cgroup; `sizeLimit` enforced by tmpfs `size=`.
- **Page cache and writeback**: large writes (checkpoints) fill dirty pages; `vm.dirty_ratio`/`dirty_background_ratio` and cgroup writeback limits cause stalls ("freezes" when flushing); tune for large-memory nodes (smaller ratios or absolute bytes: `vm.dirty_bytes`, `vm.dirty_background_bytes`); `O_DIRECT`, `fsync` strategy in checkpoint code; `posix_fadvise`/`drop_caches` only for testing.
- **Block layer**: NVMe queues and IRQ affinity, I/O schedulers (`none` for NVMe), `blk-mq`; filesystem choice (XFS for large files/parallel writes; ext4 default); mount options `noatime`; discard/trim policies.
- **Network filesystems**: NFS client (`nconnect`, rsize/wsize, `hard`/`soft`, `actimeo`), Lustre/WEKA/BeeGFS kernel clients (module versions tied to kernel and OFED!), CephFS kernel client, FUSE (S3/GCS FUSE, JuiceFS: single user-space daemon bottleneck; `fuse` device `/dev/fuse` access in containers).
- **inotify/fanotify** limits (`fs.inotify.max_user_watches`, `max_user_instances`) affect kubelet, log shippers, config reloaders: raise on busy nodes.
- **File descriptors and limits**: `fs.file-max`, `fs.nr_open`, per-process `ulimit -n` (containers inherit runtime defaults: containerd `LimitNOFILE=infinity` pitfalls with some apps), `nofile` for training processes with many open files (datasets).

## 6. Networking in the kernel

(Detailed in Part 2 and 5.10 to 5.15; summarised for the map.)

- **Devices**: veth pairs, bridges (`brctl`/`ip link add type bridge`, STP off, `hairpin_mode`), macvlan/ipvlan, VXLAN/Geneve/IPIP/WireGuard tunnels, dummy (`kube-ipvs0`), SR-IOV VFs, RDMA devices.
- **Routing**: FIB, per-netns tables, policy routing (`ip rule`) for multi-homed nodes and CNIs (Calico/Cilium), `rp_filter` (set to 0/2 on multi-NIC GPU nodes to avoid dropping asymmetric traffic), `ip_forward`, ECMP hashing policy `fib_multipath_hash_policy`.
- **Netfilter** hooks (PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING) with iptables/nftables; `br_netfilter` makes bridged traffic traverse iptables (needed by kube-proxy/NetworkPolicy on bridge CNIs); **conntrack** (`nf_conntrack_max`, buckets, timeouts), **NAT** (DNAT for Services, MASQUERADE for egress), ipset for large sets, `xt_statistic` for random LB.
- **IPVS** (`ip_vs*` modules, schedulers), **nftables** (kube-proxy nft mode).
- **eBPF**: program types used by Kubernetes networking: `sched_cls` (tc), XDP, `cgroup_sock_addr` (`connect4`, `sendmsg4`: socket LB), `sock_ops`, `sk_msg`, `cgroup_skb`, `cgroup_device`; maps (hash, LRU, LPM trie, array); verifier constraints; kernel version features (BPF host routing 5.10, netkit 6.7, BIG TCP 5.19). Inspect: `bpftool prog show`, `bpftool map dump`, `bpftool net`, `bpftool cgroup tree`.
- **tc/qdisc**: `fq`, `fq_codel`, `htb`, `netem` (testing), `clsact` for BPF; EDT for Cilium bandwidth manager.
- **Socket buffers & TCP**: `net.core.rmem_max/wmem_max`, `net.ipv4.tcp_rmem/wmem`, `tcp_congestion_control` (bbr/cubic), `tcp_mtu_probing`, `somaxconn`, `tcp_max_syn_backlog`, `ip_local_port_range`, TIME_WAIT tuning (`tcp_tw_reuse`), keepalive: namespaced per pod where allowed.
- **Offloads & queues**: GRO/GSO/TSO/LRO, checksum offload, RSS/RPS/RFS/XPS, IRQ affinity (`irqbalance` vs pinning), NAPI budgets, ring sizes (`ethtool -G`), PFC/ECN/DCQCN on RoCE NICs (Part 12).
- **RDMA stack**: `ib_core`, `rdma_cm`, `ib_uverbs`, vendor drivers (`mlx5_core`, `mlx5_ib`), `nvidia_peermem` (GPUDirect RDMA), `/dev/infiniband/*`, `ulimit -l` (memlock) and `CAP_IPC_LOCK`, IOMMU `iommu=pt` for performance, SR-IOV VF management via `devlink`.
- **Time & clocks**: `chrony`/PTP (`ptp4l`) for training logs/collectives debugging; `CLOCK_MONOTONIC` unaffected by NTP step.

## 7. CPU, memory and NUMA

- **Scheduler**: CFS (EEVDF from 6.6) with cgroup hierarchical weights; `sched_*` tunables rarely tuned; real-time classes not used by Kubernetes; `isolcpus`, `nohz_full`, `rcu_nocbs` boot parameters isolate cores for latency-sensitive pods with the static CPU manager; `cpu.idle`/`SCHED_IDLE` for best-effort; `irqaffinity` to keep IRQs off isolated cores; IRQ affinity for NICs/NVMe aligned to NUMA nodes of the device.
- **NUMA**: nodes, distances (`numactl -H`, `lscpu`), memory policies (`mbind`, `set_mempolicy`, `numa_balancing` automatic migration: disable on GPU nodes for stability, `kernel.numa_balancing=0`), device NUMA affinity (`/sys/bus/pci/devices/*/numa_node`), `cpuset.mems`; Kubernetes Topology Manager aligns CPU/memory/device (5.9). Cross-NUMA GPU↔host memory copies and NIC↔GPU paths degrade bandwidth; PCIe topology (`nvidia-smi topo -m`, `lspci -tv`).
- **Memory management**: overcommit (`vm.overcommit_memory=1` required by kubelet `protectKernelDefaults`; heuristic mode 0 may refuse large allocations), `vm.swappiness`, `vm.min_free_kbytes`, `vm.max_map_count` (large for Elasticsearch/ML: 262144+), transparent hugepages (`madvise`/`never` for databases and some latency-sensitive workloads; `always` can cause compaction stalls), explicit hugepages (`hugepages=` boot param / sysctl; 2 MiB, 1 GiB; NUMA-local allocation), KSM off, memory cgroup events, direct reclaim stalls (PSI `memory` full), `kswapd`, zone reclaim (`vm.zone_reclaim_mode=0`).
- **OOM killer**: chooses the highest `oom_score` (adjusted by `oom_score_adj`) in the cgroup (or system); logs to `dmesg` with constraint type; `vm.panic_on_oom`, `kernel.panic` (kubelet expects `kernel.panic=10` and `panic_on_oops=1` with `protectKernelDefaults`).
- **Pinned and device memory**: `mlock`/`memlock` limits; CUDA pinned host memory; GPU memory is not in cgroups (accounted by driver; per-process via `nvidia-smi`); UVM (`nvidia_uvm`) migration; Grace-Hopper unified memory; DMA-BUF.
- **Kernel memory**: slab (dentries/inodes for millions of small files), socket buffers, page tables for huge mappings; `slabtop`, `/proc/meminfo`, `/proc/slabinfo`; leaks manifest as growing non-container memory.

## 8. Devices and the GPU/RDMA stack in the kernel

- **GPU driver** (`nvidia.ko`, `nvidia_uvm.ko`, `nvidia_modeset.ko`, `nvidia_drm.ko`, `nvidia_peermem.ko`, `nvidia_fs.ko` for GDS): creates `/dev/nvidia0..N`, `/dev/nvidiactl`, `/dev/nvidia-uvm`, `/dev/nvidia-caps/*`; ioctl-based user-kernel interface; versioned: userspace `libcuda` must match the kernel driver's major interface (driver compatibility rules, 5.1); Fabric Manager manages NVSwitch; open kernel modules (`nvidia-open`) vs proprietary; kernel version coupling via DKMS/precompiled modules; Secure Boot requires signed modules; module parameters (`NVreg_*`) set in `/etc/modprobe.d`; persistence mode keeps driver state initialised.
- **IOMMU/VFIO**: `intel_iommu=on iommu=pt` (passthrough mode for host devices, performance) or full translation for VM passthrough; `/dev/vfio/*` for passing GPUs/VFs to VMs (Kata, KubeVirt, vGPU); ACS/PCIe topology and IOMMU groups constrain what can be passed through together.
- **SR-IOV/VFs**: PF driver creates VFs (`sriov_numvfs`), VFs appear as PCI devices; moved into pod netns by CNI; switchdev mode for hardware offload.
- **CDI/device cgroup**: container runtime adds device nodes and attaches the cgroup device filter (5.8).
- **udev/devtmpfs**: device node creation, permissions (`/dev/nvidia*` mode/group), rules for MIG caps and persistent names.
- **Hardware error reporting**: `rasdaemon`, EDAC (ECC memory), AER (PCIe errors) in `dmesg`, `mce` logs, Xid messages from the NVIDIA driver, NVLink error counters; GPU "falling off the bus" is a PCIe/driver event surfaced in kernel logs; nodes need these logs shipped (5.24).

## 9. Kernel versions, boot parameters and sysctls for GPU Kubernetes nodes

**Kernel version guidance** (principles; verify against your distro and driver support): use an LTS kernel with modern cgroup v2, eBPF and idmapped-mount support (5.15+ minimum, 6.1+/6.6+ preferred), supported by the NVIDIA driver, OFED and CNI you run; pin the exact kernel across the fleet; test kernel upgrades with the full stack (4.17); watch distro HWE/backport differences; avoid mixing kernels within a pool. Features by version (approximate): cgroup v2 mature ≥ 5.2, idmapped mounts 5.12, BPF cgroup improvements 5.x, `memory.oom.group` 4.19, PSI 4.20, io_uring 5.1 (disable for untrusted workloads), EEVDF 6.6, netkit 6.7, user-namespaced pods idmapped overlay 5.19.

Boot parameters (examples, adapt): `systemd.unified_cgroup_hierarchy=1`, `intel_iommu=on iommu=pt` / `amd_iommu=on iommu=pt`, `default_hugepagesz=1G hugepagesz=1G hugepages=N` (if used), `transparent_hugepage=madvise`, `numa_balancing=disable`, `isolcpus=...`/`nohz_full=...`/`rcu_nocbs=...` (only for latency-critical pinned pools), `processor.max_cstate=1 intel_idle.max_cstate=0` (latency vs power), `pci=realloc` (resizable BAR/large BARs on some platforms), `nvme_core.default_ps_max_latency_us=0`, `mitigations=` policy (security vs performance trade-off; understand impact), `audit=1`, `cgroup_no_v1=all`.

Sysctls (examples; most baseline values come from 4.17 and 5.4 chapters):

```text
vm.overcommit_memory = 1            kernel.panic = 10          kernel.panic_on_oops = 1
vm.swappiness = 1                   vm.max_map_count = 1048576  vm.min_free_kbytes = 1048576   (scale with RAM)
vm.dirty_background_bytes = 268435456   vm.dirty_bytes = 1073741824   (avoid huge write stalls)
kernel.numa_balancing = 0           kernel.pid_max = 4194304   kernel.threads-max = 4194304
fs.inotify.max_user_watches = 1048576   fs.inotify.max_user_instances = 8192   fs.file-max = 26214400
net.core.somaxconn = 65535          net.core.netdev_max_backlog = 250000
net.core.rmem_max = 268435456       net.core.wmem_max = 268435456
net.ipv4.tcp_rmem = 4096 87380 134217728   net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_mtu_probing = 1        net.ipv4.ip_local_port_range = 10240 65000
net.netfilter.nf_conntrack_max = 2097152   net.netfilter.nf_conntrack_buckets = 524288
net.ipv4.conf.all.rp_filter = 0 (or 2)     net.ipv4.ip_forward = 1   net.bridge.bridge-nf-call-iptables = 1
user.max_user_namespaces = 0 on nodes that don't need them (tradeoff with rootless/userns pods)
```

Apply via `/etc/sysctl.d/*.conf` (managed by Ansible, 4.7/4.17); kubelet `allowedUnsafeSysctls` only for specific pools; `protectKernelDefaults` to detect drift.

Kernel modules for Kubernetes nodes: `overlay`, `br_netfilter`, `nf_conntrack`, `nf_nat`, `ip_vs*` (IPVS), `vxlan`, `wireguard`, `xt_*`/`nft_*`, `ip_tables`, `rdma_cm`/`ib_*`/`mlx5_*`, `nvidia*`, `nvme_tcp`/`nvme_rdma` (NVMe-oF), `fuse`, `lustre`/`wekafs` clients, `vfio_pci`, `tun`.

## 10. Observing the kernel from Kubernetes

| Need | Tool/Source |
|---|---|
| Where is time going in the kernel? | `perf top`, `perf record -g`, `bpftrace`, `bcc`/`libbpf-tools` (`runqlat`, `biolatency`, `tcpconnlat`, `tcpretrans`, `opensnoop`, `execsnoop`, `oomkill`) |
| Per-container kernel metrics | cAdvisor (cgroup files), node-exporter (`/proc`), `kubelet /metrics/resource`, PSI exporters |
| Syscalls, files, network | `strace -f`, `ltrace`, `tcpdump`, `ss`, `lsof`, `fatrace` |
| Kernel logs | `dmesg -T`, `journalctl -k`, `/var/log/kern.log`, remote log shipping; `rasdaemon`, `mcelog` |
| Security/auditing | auditd (`execve`, `openat` on secrets), Falco/Tetragon (eBPF), seccomp audit logs |
| Latency of scheduling | `perf sched`, `runqlat`, `sched:` tracepoints; PSI cpu |
| Memory issues | `/proc/meminfo`, `smem`, `slabtop`, `numastat`, `memory.stat`, `perf mem`, `bpftrace` oom tracepoints |
| Tracing Kubernetes-aware | Pixie, Inspektor Gadget (`kubectl gadget trace tcp/dns/oomkill/exec/open`), Tetragon, Hubble |

```bash
# Inspektor Gadget examples (eBPF gadgets scoped to pods)
kubectl gadget trace oomkill; kubectl gadget trace tcpconnect -n serving; kubectl gadget profile cpu -n training --podname trainer-0
# Common bcc/libbpf tools on the node
runqlat 10 1; biolatency -D 10 1; tcpretrans; tcplife; cachestat; oomkill
```

## 11. Failure modes mapped to kernel causes

| Symptom in Kubernetes | Kernel cause | How to confirm |
|---|---|---|
| Container exit 137 | cgroup memory OOM or SIGKILL by kubelet/runtime | `memory.events oom_kill`, `dmesg` "Memory cgroup out of memory" |
| Latency spikes at low CPU % | CFS throttling | `cpu.stat nr_throttled`, `container_cpu_cfs_throttled_*` |
| `fork: retry: Resource temporarily unavailable` | `pids.max` or `kernel.pid_max` | `pids.events`, `/proc/sys/kernel/pid_max` |
| `Too many open files` | `ulimit -n`, `fs.file-max`, inotify limits | `/proc/PID/limits`, `sysctl fs.inotify` |
| Intermittent connection drops | conntrack table full, insert failures, SYN backlog overflow | `conntrack -S`, `nstat ListenOverflows` |
| Large transfers stall | MTU/PMTUD blackhole, offload bugs | `ping -M do`, `ethtool -k`, capture |
| Pods can't connect after rule changes | netfilter/iptables lock contention, kube-proxy sync, stale conntrack | kube-proxy logs, `iptables --wait`, conntrack flush |
| Mount failures / stale handles | NFS server issues, FUSE crash, namespace propagation | `dmesg`, `findmnt`, `mountstats` |
| Directory/file operations slow in container | overlayfs copy-up/metadata, many small files, dentry cache pressure | move data to volume, `slabtop`, `perf` |
| Process unkillable | D-state on hung I/O or driver | `/proc/PID/stack`, kernel logs, storage health |
| GPU lost after kernel update | DKMS build failed/unsigned module/ABI mismatch | `dkms status`, `modinfo nvidia`, journal |
| `Operation not permitted` in a container | seccomp, missing capability, LSM denial, user namespace restrictions | `strace` EPERM, audit logs, `capsh`, `aa-status` |
| Node unresponsive under load | Memory pressure without reservations, softlockups, IRQ storms | PSI, `dmesg`, `perf`, `mpstat -I` |
| NUMA-related low throughput | Cross-socket memory/device access, `numa_balancing` | `numastat -p`, `nvidia-smi topo -m`, `perf stat` |
| Clock skew / odd timeouts | NTP failure, VM time drift | `chronyc tracking`, `timedatectl` |

## 12. Lab (untested)

1. **Build a container by hand**: create a rootfs, then use `unshare -fp --mount-proc --mount --net --uts --ipc`, `pivot_root`, a cgroup v2 directory with `cpu.max`, `memory.max`, `pids.max`, and device allow-list via `bpftool`/`systemd-run -p DeviceAllow=` equivalents; compare with `runc`.
2. **Namespace tour**: for a pod, list namespaces with `lsns`; compare inode numbers across containers of one pod and a different pod; join each with `nsenter` and run commands; show `shareProcessNamespace` effect.
3. **cgroup experiments**: create pods with CPU/memory/pids limits; read cgroup files; cause throttling (multi-threaded burn) and measure `nr_throttled`; trigger OOM and read `memory.events`; compare `memory.current` vs working set; show tmpfs charged to the cgroup.
4. **Device filter**: run a GPU pod and a non-GPU pod; compare `/dev` contents and attempt to open `/dev/nvidia0` from the other pod's namespace (`nsenter -m`) to see cgroup device denial; inspect the BPF program with `bpftool cgroup tree`.
5. **Security layers**: run containers with different caps/seccomp/no_new_privs and demonstrate failures for mount, ptrace, raw sockets, `setuid`; read status files; test a custom seccomp profile; (SELinux nodes) trigger and read an AVC denial.
6. **overlayfs behaviour**: write a large file in the container layer vs a volume; measure copy-up cost modifying a 5 GB image file; look at `lowerdir/upperdir` in `/proc/mounts`.
7. **Netfilter/eBPF**: dump kube-proxy rules for a Service; with Cilium dump BPF LB maps; trace a connection with `bpftrace`/`tcpconnect`; observe conntrack entries; measure the effect of `nf_conntrack_max` exhaustion.
8. **Memory and NUMA**: on a two-socket node, run a memory benchmark pinned to local vs remote NUMA; show `numa_balancing` impact; enable hugepages and a pod requesting them; inspect `hugetlb` cgroup files.
9. **Writeback stall**: write a large checkpoint-sized file with default `vm.dirty_*` and observe stalls (`iostat`, app timing); tune and compare.
10. **Version matrix**: record kernel, cgroup mode, driver, OFED, CNI versions on a node; check feature availability list from section 9; plan an upgrade test.
11. **eBPF observability**: install Inspektor Gadget or bcc tools; trace `oomkill`, `execsnoop`, `tcpretrans`, `runqlat` while running load in pods; correlate to symptoms.
12. **Sysctl audit**: gather `sysctl -a` from a GPU node and compare with the baseline in section 9; list deviations and whether each is safe; encode the baseline in Ansible (4.7) with `protectKernelDefaults` verification.
13. **Clean up**.

Mark tested only after execution.

## 13. Common mistakes

- Thinking containers have their own kernel; assuming namespace isolation equals VM isolation.
- Setting CPU limits equal to a small request on multi-threaded ML processes and wondering why latency is bad.
- Counting only RSS when sizing memory limits (ignoring tmpfs, page cache, pinned memory, kernel memory).
- Using cgroup v1 assumptions/tools on v2 hosts (and vice versa); old runtimes on v2.
- Running mixed kernels across a GPU pool; upgrading the kernel without validating driver/OFED/CNI/CSI modules.
- Ignoring conntrack, inotify and PID limits until the node falls over.
- Leaving THP `always`, NUMA balancing on, or default dirty-page ratios on large-memory GPU nodes.
- Assuming `privileged: true` is how to "make GPUs work" instead of proper device exposure.
- Treating seccomp/LSM failures as application bugs.
- Not shipping kernel logs (Xid, EDAC, AER) off the node.

## 14. Interview angles

- "What is a container at the kernel level? Which kernel features does Kubernetes use for isolation and limits?" 
- "How does the kernel enforce CPU and memory limits? Why does CPU throttling happen at low average usage?" 
- "What happens in the kernel when a container exceeds its memory limit? How is it different from node-pressure eviction?" 
- "How does a Service get implemented in the kernel under iptables, IPVS, and eBPF?" 
- "How does a GPU device get into a container and what stops other containers from using it?" 
- "Which sysctls and boot parameters do you set on GPU nodes and why?" 
- "What are the container-escape surfaces and how do seccomp/capabilities/user namespaces reduce them?" 
- "How would you diagnose a node that's slow but whose pods look healthy?" (PSI, softirq, IO wait, throttling, NUMA.)

## 15. Checkpoint questions (40)

1. Namespaces count? **A:** Eight (mnt, pid, net, uts, ipc, user, cgroup, time).
2. What keeps a namespace alive? **A:** Member process, open fd, or bind mount.
3. Pod shares which namespaces? **A:** net, ipc, uts (pid optional).
4. PID 1 signal behaviour? **A:** Ignores signals without handlers.
5. cgroup v2 hierarchy? **A:** Single unified tree.
6. `cpu.max` format? **A:** `quota period`.
7. `cpu.weight` from? **A:** CPU requests.
8. Throttling metric? **A:** `nr_throttled`/`throttled_usec`.
9. `memory.max` is? **A:** Hard limit.
10. `memory.high` is? **A:** Soft throttle threshold.
11. OOM evidence file? **A:** `memory.events`.
12. tmpfs charged to? **A:** The cgroup's memory.
13. `pids.max` set by? **A:** `podPidsLimit`.
14. cpuset used for? **A:** Exclusive CPUs/NUMA pinning.
15. Device access in v2? **A:** BPF cgroup device programs.
16. Capabilities default set size? **A:** ~14 caps.
17. `no_new_privs` effect? **A:** Blocks privilege gain on exec.
18. seccomp RuntimeDefault blocks? **A:** Dangerous syscalls (~40+).
19. LSMs? **A:** AppArmor/SELinux.
20. User namespace benefit? **A:** Root in container is unprivileged on host.
21. overlayfs layers? **A:** lowerdirs + upperdir + workdir.
22. Copy-up means? **A:** Whole-file copy to upper layer on first write.
23. Bind mount propagation `Bidirectional` used by? **A:** CSI node plugins.
24. `/dev/shm` type? **A:** tmpfs.
25. veth is? **A:** Virtual Ethernet pair.
26. Services via? **A:** netfilter NAT/IPVS/eBPF.
27. conntrack role? **A:** Tracks flows for NAT/stateful filtering.
28. `br_netfilter` needed for? **A:** Bridged traffic through iptables.
29. eBPF program types in CNI? **A:** tc, XDP, cgroup sock_addr.
30. tc qdisc for shaping? **A:** htb/fq (EDT).
31. `nvidia_peermem` enables? **A:** GPUDirect RDMA.
32. IOMMU passthrough param? **A:** `iommu=pt`.
33. NUMA balancing on GPU nodes? **A:** Usually disable.
34. THP recommendation? **A:** `madvise`/`never` for sensitive workloads.
35. `vm.overcommit_memory` for kubelet? **A:** 1.
36. PSI files? **A:** `/proc/pressure/{cpu,memory,io}`.
37. Dirty page tuning goal? **A:** Avoid long writeback stalls.
38. Why pin kernel versions? **A:** Driver/OFED/CNI compatibility.
39. Kernel logs to watch on GPU nodes? **A:** Xid, EDAC, AER, MCE.
40. eBPF debugging tool for pods? **A:** Inspektor Gadget/bcc tools.

## 16. Sources and review notes

**Written in original words.** Principal sources:

- Brian Ward, *How Linux Works* (3rd edition; chapter 17 on virtualization/containers, kernel and device chapters).
- James Strong and Vallery Lancey, *Networking and Kubernetes* (chapters 2 to 5: Linux networking, container networking, Kubernetes networking).
- Josh Rosso et al., *Production Kubernetes* (chapters 3 to 5 on runtime and networking).
- Linux kernel documentation (cgroup-v2, namespaces, seccomp, overlayfs, BPF), man pages (`namespaces(7)`, `cgroups(7)`, `capabilities(7)`), NVIDIA driver and Container Toolkit documentation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** all kernel version thresholds (idmapped mounts, EEVDF, netkit, BPF features), cgroup file names for your kernel, default capability set per runtime version, recommended sysctl values (scale with hardware), and every command listing; all labs are **untested**.
