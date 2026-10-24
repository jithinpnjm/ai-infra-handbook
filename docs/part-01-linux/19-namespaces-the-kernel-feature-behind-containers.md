---
id: "c01-19"
title: "1.19 Namespaces: the kernel feature behind containers"
sidebar_label: "1.19 Namespaces: the kernel feature behind containers"
sidebar_position: 19
description: "Namespaces: the kernel feature behind containers"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 1.19 Namespaces: the kernel feature behind containers

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | GCP / GKE (an Ubuntu VM; root needed) |
| Part | Part 1: Linux, from the command line to the kernel and performance |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Almost every AI workload on a modern cluster runs in a container: a Kubernetes pod, an Enroot/Pyxis container under Slurm, a Docker image on a developer box. If you do not know what a container *is* at the kernel level, you cannot debug it. Typical failures all trace back to this chapter:

- A training script started with `bash -c` never checkpoints on `SIGTERM` because it is PID 1 of a PID namespace and the kernel gives PID 1 no default signal actions.
- `nproc`, `free` and `top` inside a pod show the **host's** 128 CPUs and 2 TiB while the cgroup allows 8 CPUs and 64 GiB.
- Two pods on the same node cannot use shared memory (NCCL SHM, MPI) between them because their IPC namespaces differ.
- A pod loses its network, or `hostNetwork: true` changes how InfiniBand and NCCL behave.
- File ownership on NFS or Lustre is wrong because user namespaces remap UIDs.
- An image-layer write of a multi-gigabyte file fills `/var/lib/containerd` (overlayfs copy-up).
- Security reviews ask "is this container privileged? does it share the host PID namespace? is the user namespace remapped?"

Chapter 1.18 explained *limiting* what a process can use (cgroups). This chapter explains *limiting what it can see*: **namespaces**. Together with a root filesystem, capabilities and seccomp (chapter 1.21), they are what a container is. Chapter 1.20 puts them together in a hands-on lab that builds a container by hand.

## Prerequisites and outcomes

You should know processes and signals (1.8), the mount/filesystem model (1.12), kernel interfaces (1.10), and cgroups (1.18). Networking details used here (bridges, veth, NAT) are developed fully in Part 2; this chapter gives just enough.

After this chapter you can:

- State precisely what a container is and is not: a process (tree) with a set of namespaces, a cgroup, a root filesystem, a reduced privilege set, all sharing the host kernel.
- List the eight namespace types, what each isolates, and the system calls that create or join them (`clone`, `unshare`, `setns`).
- Inspect a process's namespaces (`/proc/PID/ns`, `lsns`, `nsenter`) and create your own (`unshare`).
- Explain PID namespace semantics (PID 1 behaviour, zombie reaping, signal rules), mount namespaces and propagation, `chroot` versus `pivot_root`, and OverlayFS layers, copy-up and whiteouts.
- Explain network namespaces, veth pairs, bridges and NAT, and how pods share namespaces.
- Explain user namespaces, UID mapping, rootless containers and their limitations.
- Compare containers, VMs and lightweight (micro)VMs and know the isolation, performance and observability trade-offs.
- Identify and avoid the common pitfalls: host-view tools inside containers, PID 1 handling, large writes to the image layer, tracing limitations.

## 1. A container is not a kernel object

The Linux kernel has **no object called a container**. A "container" is user-space tooling (Docker, containerd with runc, Podman, LXC, Enroot) that composes several independent kernel features:

| Feature | What it controls | Chapter |
|---|---|---|
| **Namespaces** | What the process *sees* (processes, mounts, network, hostname, IPC, users, cgroup view, clocks) | this one |
| **cgroups** | What the process may *use* (CPU, memory, I/O, PIDs, devices) | 1.18 |
| **Root filesystem** | Its own `/` (an image unpacked or overlaid, entered with `pivot_root`) | this one |
| **Capabilities, seccomp, LSMs** | What it may *do* (privileged operations, system calls, files by label/profile) | 1.21 |

```mermaid
flowchart TB
  subgraph Host["One Linux kernel, one set of drivers (including the NVIDIA driver)"]
    direction TB
    subgraph C1["Container A (a process tree)"]
      A1["pid ns · mnt ns · net ns · uts ns · ipc ns · user ns · cgroup ns"]
      A2["cgroup: cpu/mem/io/pids limits"]
      A3["rootfs: overlay of image layers"]
      A4["capabilities + seccomp + AppArmor/SELinux"]
    end
    subgraph C2["Container B"]
      B1["its own namespaces, cgroup, rootfs, filters"]
    end
    K["Shared kernel: scheduler, memory manager, drivers, network stack"]
  end
  C1 --> K
  C2 --> K
```

Gregg's way of putting it: the kernel keeps a pointer (`struct nsproxy`) from each task to its namespaces; that structure is the closest thing the kernel has to a "container". Because the kernel is shared, a container starts in milliseconds, uses no guest-kernel memory, has no virtualisation overhead on CPU or memory, and calls the GPU driver natively. The price: all containers contend for the same kernel locks, caches and queues (noisy neighbours), a kernel bug or panic affects every container, guests cannot load their own kernel modules or run a different kernel, and isolation is weaker than hardware virtualisation because the attack surface is the whole system-call interface.

History in one paragraph: `chroot` (Unix V7, 1979) changed a process's idea of `/`; FreeBSD jails (1998) and Solaris Zones (2005) added whole-system partitioning; Linux added mount namespaces in 2.4.19 (2002) and then, over many releases, the other namespace types; cgroups arrived in 2.6.24 (2008); LXC (2008) and Docker (2013) packaged these; the OCI specification standardised the image and runtime format; Kubernetes (2014) became the orchestrator.

## 2. The namespace types

A **namespace** wraps a global system resource so that processes inside it see their own isolated instance. Changes inside are visible only to members. Every process is always in exactly one namespace of each type (initially the host's "init" namespaces).

| Namespace | Clone flag | Isolates | Notes |
|---|---|---|---|
| **mnt** | `CLONE_NEWNS` | Mount points (the filesystem tree as seen) | First namespace (2002), hence the odd flag name |
| **pid** | `CLONE_NEWPID` | Process ID numbering and visibility (`/proc` content) | First process is PID 1 inside; nests hierarchically |
| **net** | `CLONE_NEWNET` | Network devices, IP addresses, routes, firewall rules, sockets, ports, `/proc/net` | A new one has only a down `lo` |
| **uts** | `CLONE_NEWUTS` | Hostname and NIS domain name (`uname`) | "UNIX Time-sharing System" |
| **ipc** | `CLONE_NEWIPC` | System V IPC objects and POSIX message queues | Shared memory segments (`shmget`) |
| **user** | `CLONE_NEWUSER` | UID/GID number space, capabilities | Root inside can be an unprivileged user outside |
| **cgroup** | `CLONE_NEWCGROUP` | The view of the cgroup hierarchy root | Container sees its own cgroup as `/` |
| **time** | `CLONE_NEWTIME` | `CLOCK_MONOTONIC`/`CLOCK_BOOTTIME` offsets | Added in Linux 5.6; rarely used |

Three system calls do all the work:

- **`clone(2)`** (and `clone3`) creates a new process, optionally in new namespaces (`CLONE_NEW*` flags). This is how runtimes start a container's first process.
- **`unshare(2)`** moves the *calling* process into new namespaces (for PID namespaces, only its *future children* enter the new one). The `unshare(1)` command wraps it.
- **`setns(2)`** joins an *existing* namespace through a file descriptor from `/proc/PID/ns/*`. `nsenter(1)` wraps it, and `docker exec`/`kubectl exec` are essentially "setns into the container's namespaces and exec a program".

A namespace lives as long as something references it: a process in it, an open file descriptor to `/proc/PID/ns/xxx`, or a bind mount of that file (which is how `ip netns` keeps named network namespaces under `/run/netns` alive with no process).

### Inspecting namespaces

```bash
ls -l /proc/$$/ns/                     # symlinks like net:[4026531992]; the number is the namespace inode
readlink /proc/$$/ns/net               # compare two processes: same number = same namespace
lsns                                   # list all namespaces, number of processes, first process
lsns -t net                            # only network namespaces
sudo lsns -p 1234                      # the namespaces of PID 1234
sudo nsenter -t 1234 -n ip addr        # run `ip addr` in PID 1234's network namespace
sudo nsenter -t 1234 -m -u -i -n -p /bin/sh   # approximately what `docker exec` does
cat /proc/self/uid_map /proc/self/gid_map     # user namespace mappings (see section 6)
cat /proc/sys/user/max_user_namespaces        # per-user limits (user.max_*_namespaces)
```

Practical debugging recipe for Kubernetes: find the container's host PID (`crictl inspect <id> | grep -i pid`, or `docker inspect -f '{{.State.Pid}}'`), then `nsenter -t PID -n` to run host tools (tcpdump, ss, ethtool) *inside the pod's network namespace* even when the image has no such tools. This is one of the most useful skills in this chapter.

## 3. PID namespaces

A PID namespace gives its members a private PID numbering. The first process in it is **PID 1**; it sees only itself and its descendants in `/proc` (once `/proc` is mounted from inside that namespace). The same process has *different PIDs in different namespaces*: PID 1 in the container may be PID 45982 on the host. PID namespaces nest: a parent namespace sees all descendants (with its own numbers); a child sees nothing above it.

```mermaid
flowchart TB
  subgraph H["Host PID namespace"]
    H1["PID 1 systemd"]
    H2["PID 2140 containerd-shim"]
    subgraph Cns["Container PID namespace"]
      C1["host PID 45982 = PID 1 inside\n(bash / python train.py)"]
      C2["host PID 45990 = PID 7 inside\n(data loader worker)"]
    end
    H2 --> C1
    C1 --> C2
  end
```

Special behaviour of PID 1 (the "init" of the namespace):

1. **No default signal actions.** Signals sent *from inside the namespace* to PID 1 are only delivered if PID 1 installed a handler for them; `SIGKILL` and `SIGSTOP` from inside are ignored. From the parent namespace they work (that is how `docker stop`, `kubectl delete pod` and the kubelet's `SIGTERM` then `SIGKILL` reach it). Consequence: a shell script as PID 1 that installed no `SIGTERM` handler ignores the termination request; the runtime waits out the grace period (30 s in Kubernetes by default) then sends `SIGKILL`. A training job loses its chance to checkpoint. Use `exec python train.py` as the script's last command so the program itself becomes PID 1 and installs its own handler, or use a tiny init (`tini`, `docker run --init`, `dumb-init`, Kubernetes `shareProcessNamespace`).
2. **Reaping orphans.** Orphans in the namespace are re-parented to PID 1, which must call `wait()`; if it does not, zombies accumulate (eventually exhausting the PID limit, chapter 1.18 `pids.max`). Real init programs reap; application PID 1s often do not (chapter 1.8 zombies).
3. **When PID 1 exits, the kernel kills every other process in that namespace** (`SIGKILL`), and the namespace becomes unusable for new forks. This is why a container dies when its main process dies.

`unshare --pid` only affects *children*: to have the shell itself be PID 1 use `--fork`. Also `/proc` is a mount; after creating a PID namespace you must mount a fresh `proc` (`mount -t proc proc /proc`, or `unshare --mount-proc`) in a mount namespace, otherwise tools like `ps` still show the host's view.

Kubernetes ties these together: the pod's `pause` (infra) container holds the pod's shared namespaces; with `shareProcessNamespace: true` all containers in the pod share one PID namespace and `pause` runs as PID 1 and reaps zombies. `hostPID: true` puts the pod in the **host** PID namespace (needed for some profilers and node agents, and a strong security exposure).

## 4. Mount namespaces, root changes and OverlayFS

### Mount namespaces and propagation

A new mount namespace starts with a **copy** of its parent's mount table. Later mounts and unmounts inside do not affect the other namespace, subject to **propagation flags** on each mount point:

| Flag | Meaning |
|---|---|
| `shared` | Mount/unmount events propagate to and from peer mounts |
| `slave` | Receives events from the master, sends none |
| `private` | No propagation either way |
| `unbindable` | Private and cannot be bind-mounted |

`systemd` makes `/` shared by default, so a naive new mount namespace can leak mounts back to the host; container runtimes therefore remount the root `rslave` or `rprivate` first (`unshare --propagation private` or `mount --make-rprivate /`). Kubernetes `mountPropagation: HostToContainer` (rslave) lets a pod see mounts created later on the host (CSI drivers rely on this); `Bidirectional` (rshared) lets the container create mounts visible on the host and needs privileged mode. Inspect with `findmnt -o TARGET,PROPAGATION` and `cat /proc/self/mountinfo` (optional fields show `shared:N`, `master:N`).

### chroot versus pivot_root

`chroot(2)` changes a process's root directory but keeps the old root reachable through open file descriptors or by `fchdir` tricks if the process has root privilege; it is a convenience, not a security boundary. Container runtimes instead create a mount namespace, set up the new root, and call **`pivot_root(2)`**, which swaps the root mount and lets the old root be unmounted and detached completely. The sequence for a minimal container: new mount namespace → make mounts private → bind-mount the new rootfs on itself → mount `proc`, `sysfs` (read-only), `tmpfs` for `/dev`, device nodes → `pivot_root` into it → unmount the old root → drop capabilities → exec the program. Sensitive host paths (`/proc/kcore`, `/sys/firmware`, parts of `/proc/sys`) are masked or read-only (the "masked paths" in the OCI spec).

### OverlayFS: images as layers

A container image is an ordered stack of **read-only layers** (each a tar of filesystem changes, content-addressed by hash). To run a container the runtime mounts them with **OverlayFS**, a union filesystem built into the kernel:

- `lowerdir=` one or more read-only directories (the image layers; colon-separated, **leftmost is topmost**);
- `upperdir=` the read-write layer, initially empty, where all changes land;
- `workdir=` an empty scratch directory on the same filesystem as `upperdir`, used for atomic operations;
- the **merged** view is what the container sees as `/`.

```bash
mkdir -p lower1 lower2 upper work merged
echo "from layer 1" > lower1/a.txt ; echo "from layer 2" > lower2/a.txt ; echo only-in-2 > lower2/b.txt
sudo mount -t overlay overlay -o lowerdir=lower2:lower1,upperdir=upper,workdir=work merged
cat merged/a.txt                  # "from layer 2": upper layers hide lower ones
echo changed > merged/a.txt       # copy-up: file copied to upper, then modified
ls upper                          # a.txt now exists in upper; lower1/lower2 unchanged
rm merged/b.txt ; ls -l upper/b.txt   # a whiteout: a character device 0/0 hides the lower file
mount | grep overlay              # compare with a running container's root: docker run --rm alpine mount | head -1
```

Key behaviours:

- **Copy-up**: the first write to a file that lives in a lower layer copies the *entire file* to the upper layer (metadata-only changes copy only metadata on modern kernels with `metacopy`). A training job that appends to a multi-GB file baked into an image, or a database in the image layer, triggers a huge copy, doubles disk use, and can fill the node's image storage (`/var/lib/containerd` or `/var/lib/docker`), causing evictions and `NodeNotReady`. **Mutable and large data belongs in volumes** (bind mounts, `emptyDir`, hostPath, PVCs), which bypass overlay completely.
- **Whiteouts**: deleting a lower file creates a 0/0 character device (or an opaque-directory xattr for removed directories) in the upper layer; the lower data remain on disk. Deleting a file in a later Dockerfile layer **does not shrink the image**: the earlier layer still holds the bytes, which is why secrets baked into a layer and "deleted" later remain extractable.
- **Performance**: metadata-heavy operations (`stat`, `readdir`) cost more through overlay; random I/O on the image layer is slower than on a raw filesystem. Cache layers (e.g. package caches) should be volumes; model weights and datasets should be mounted, not copied into images. The Gregg book shows a kernel stack where a container write goes through `ovl_write_iter` before reaching XFS: the filesystem below matters (overlayfs needs `d_type` support; XFS needs `ftype=1`).
- **Page cache sharing**: containers from the same image share lower-layer files and their page cache, saving memory relative to VMs.
- **Rootless mode** uses `fuse-overlayfs` on older kernels (slower); kernel 5.11+ allows unprivileged overlay mounts inside user namespaces.
- Other storage drivers exist (`btrfs`, `zfs`, `devicemapper`, containerd snapshotters including `stargz` lazy-pulling); on Kubernetes nodes overlayfs through containerd's snapshotter is the norm.

Image *build* notes (Docker/OCI): each `RUN`/`COPY` step creates a layer; many layers slow mounting; combine steps and use multi-stage builds to keep build tools out of the final image; pin base image tags or digests (`latest` is not reproducible); an image's `ENTRYPOINT`/`CMD` define PID 1 (use the exec form `["python","train.py"]`, not shell form, so there is no wrapping `sh`). Docker keeps stopped containers and old images by default: `docker ps -a`, `docker system df`, `docker system prune` (with care).

## 5. Network namespaces

A new network namespace contains nothing but a loopback interface in the DOWN state: no devices, routes or firewall rules. It has its own IP addresses, routing tables, ARP table, `iptables`/`nftables` rules, sockets and port space (two containers can both listen on port 80), and its own `/proc/net`. Moving a physical or virtual interface into a namespace removes it from the original one.

The standard way to connect it is a **veth pair**: a virtual Ethernet cable whose two ends are separate interfaces. One end stays in the host namespace and is attached to a **bridge** (`docker0`, `cni0`, or a CNI plugin's equivalent) or routed; the other is moved into the container's namespace and renamed `eth0` with an address. Traffic leaving the host to the outside is typically **NAT**ed (masquerade) by iptables/nftables, and published ports are DNAT rules.

```mermaid
flowchart LR
  subgraph HostNS["Host network namespace"]
    ETH["eth0 / ens… (physical NIC)"]
    BR["bridge docker0 / cni0\n172.17.0.1"]
    V1["vethA (host end)"]
    V2["vethB (host end)"]
    NAT["iptables / nftables\nMASQUERADE + DNAT"]
  end
  subgraph NS1["Container net ns A"]
    E1["eth0 172.17.0.2"]
  end
  subgraph NS2["Container net ns B"]
    E2["eth0 172.17.0.3"]
  end
  E1 --- V1 --- BR
  E2 --- V2 --- BR
  BR --- NAT --- ETH
```

```bash
sudo ip netns add demo                              # named network namespace (bind-mounted under /run/netns)
sudo ip link add vethH type veth peer name vethC    # a veth pair in the host namespace
sudo ip link set vethC netns demo                   # move one end in
sudo ip addr add 10.9.0.1/24 dev vethH && sudo ip link set vethH up
sudo ip netns exec demo ip addr add 10.9.0.2/24 dev vethC
sudo ip netns exec demo ip link set vethC up ; sudo ip netns exec demo ip link set lo up
sudo ip netns exec demo ping -c2 10.9.0.1
sudo ip netns exec demo ip route add default via 10.9.0.1        # then enable forwarding + NAT on the host
ip -br link ; sudo ip netns exec demo ip -br link
sudo ip netns del demo
```

Variants you will meet:

- **Pod networking in Kubernetes**: all containers of a pod share one network namespace (created by the pause container); a **CNI plugin** (Calico, Cilium, Flannel, and so on) creates the veth, assigns the pod IP and installs routes or tunnels. `hostNetwork: true` puts the pod in the *host's* namespace (no isolation; used by node agents and sometimes by performance-sensitive jobs).
- **Docker modes**: `bridge` (default), `host`, `none`, `container:<id>` (join another container's namespace), `macvlan`/`ipvlan` (give the container an address directly on the physical network).
- **Rootless Podman** cannot create veth pairs without privilege, so it uses a user-space TCP/IP stack (`slirp4netns` or `pasta`): lower throughput and containers cannot reach each other the same way.
- **High-performance fabrics**: SR-IOV virtual functions or RDMA devices can be moved into a container's namespace (Multus, SR-IOV CNI, `rdma-shared-device-plugin`); RDMA in containers needs the right device files, the host IB stack and, with shared-mode RDMA, the RDMA subsystem's own namespace mode (`rdma system set netns exclusive|shared`). `hostNetwork` is frequently used with NCCL over InfiniBand to avoid NAT and the CNI path. Details in Parts 2, 8 and 9.
- **Tracing**: `ss`, `tcpdump`, `ethtool` can be run from the host with `nsenter -t PID -n` or `ip netns exec`.

## 6. User namespaces, UID mapping and rootless containers

A user namespace has its own UID/GID number space and **its own capability set**. The kernel keeps a mapping table (`/proc/PID/uid_map`, `gid_map`: `inside_start outside_start length`). Process "root" (UID 0) in the namespace can be UID 100000 on the host, so even if it escapes the container it is an unprivileged user outside. Inside, it has capabilities **only over resources owned by that namespace** (it can mount in its own mount namespace, configure its own network namespace) but not over the host. Hence an unprivileged user can create a user namespace and, within it, other namespaces: this is the basis of **rootless containers** (Podman, rootless Docker, Enroot, Apptainer/Singularity in user-namespace mode).

```bash
unshare --user --map-root-user bash        # become "root" inside, mapped to your UID outside
id; cat /proc/self/uid_map                 # uid 0 inside = your uid outside
touch /root-owned 2>&1                     # no real privilege: fails on host-owned paths
exit
cat /etc/subuid /etc/subgid                # subordinate ID ranges allotted to each user (newuidmap/newgidmap)
```

The trade-offs matter for HPC/AI: files on shared storage (NFS, Lustre, GPFS, BeeGFS) are owned by real UIDs, and ID-mapped access through a user namespace can break ownership, permissions and quotas; kernel features like ID-mapped mounts (5.12+) and filesystem support vary. That is why many clusters run containers as the real user (Enroot/Pyxis, Apptainer's setuid or "fakeroot" modes) or as privileged/root containers with security profiles (AppArmor, SELinux, seccomp; chapter 1.21) rather than user-namespace remapping. Kubernetes user-namespace support (`hostUsers: false`) is newer and feature-gated; verify its status for your version. User namespaces also enlarge the kernel attack surface, so some distributions restrict unprivileged creation (`kernel.unprivileged_userns_clone`, Ubuntu's AppArmor restriction in recent releases; flag: check your distribution).

## 7. UTS, IPC, cgroup and time namespaces

- **UTS**: the container has its own hostname (`hostname`, `uname -n`); Kubernetes sets it to the pod name. Changing it inside does not affect the host. Gregg notes the UTS nodename is a convenient container identifier for BPF tools.
- **IPC**: System V shared memory, semaphores and message queues, plus POSIX message queues, are namespaced. **Containers in different IPC namespaces cannot share SysV segments.** Within a pod all containers share the IPC namespace by default (`hostIPC: true` joins the host's). NCCL, MPI and PyTorch data-loader workers use shared memory heavily: PyTorch's `DataLoader` uses `/dev/shm` (tmpfs; Docker defaults it to 64 MiB, a classic cause of "bus error" crashes in containers: raise it with `--shm-size`, `--ipc=host` or an `emptyDir` with `medium: Memory`). MPI ranks in *separate pods* on the same node fall back to network paths because they do not share IPC.
- **Cgroup namespace**: makes `/proc/self/cgroup` and `/sys/fs/cgroup` show the container's cgroup as the root (`0::/`), hiding the host's cgroup path layout. It changes the *view*, not the limits (chapter 1.18).
- **Time namespace**: per-container offsets of the monotonic and boot clocks (not wall time); used for checkpoint/restore (CRIU) migration.

## 8. Putting it together: what a runtime does

When `docker run` or the kubelet asks containerd/runc to start a container, the sequence (simplified) is:

```mermaid
sequenceDiagram
  participant K as kubelet / docker CLI
  participant CD as containerd
  participant SH as containerd-shim
  participant RC as runc (OCI runtime)
  participant KN as Linux kernel
  K->>CD: create container (image, config)
  CD->>CD: unpack layers, prepare overlay snapshot
  CD->>SH: start shim (stays as parent)
  SH->>RC: run with OCI bundle (config.json + rootfs)
  RC->>KN: clone(CLONE_NEWPID|NEWNS|NEWNET|NEWUTS|NEWIPC|…)
  RC->>KN: create cgroup, write limits (ch. 1.18)
  RC->>KN: mount rootfs, pivot_root, mask paths
  RC->>KN: set capabilities, seccomp filter, LSM label (ch. 1.21)
  RC->>KN: execve(user process) as PID 1
  RC-->>SH: exit (runc is gone, shim supervises)
  Note over SH,KN: CNI plugin is called to create the net ns wiring
```

The **OCI runtime spec** (`config.json`) lists every namespace, mount, capability, cgroup path and hook; `runc spec` generates a template, and reading a real container's `config.json` is the best way to learn what your platform configures. The **shim** keeps the container's stdio and exit status after `runc` exits, so containerd can restart without killing containers.

## 9. Containers, VMs and lightweight VMs

| | Hardware VM (KVM/QEMU) | Container | MicroVM (Firecracker, Kata) | User-space kernel (gVisor) |
|---|---|---|---|---|
| Kernel | Own guest kernel | Shared host kernel | Own minimal guest kernel | Go "kernel" intercepting syscalls |
| Isolation | Strong (hardware, small VMM interface) | Weaker (whole syscall surface, kernel bugs) | Strong, with hardware boundary | Medium, high overhead for syscall-heavy loads |
| Start time | Seconds | Milliseconds | About 100 to 200 ms | Milliseconds |
| Memory overhead | Hundreds of MiB (guest kernel, QEMU) | Near zero | Few MiB (Firecracker) to tens of MiB (Kata) | Moderate |
| Observability | Guest has its own `/proc`, tracing works inside | Tools inside often show **host** statistics; tracing mostly blocked | Like VMs | Limited |
| GPU access | Passthrough (VFIO) or vGPU/MIG | Native driver access via device nodes | Passthrough possible but complex | Limited |
| Typical use | Cloud instances, isolation of tenants | Microservices, ML jobs, CI | Serverless, multi-tenant sandboxes, Kata for strong pod isolation | Sandboxing untrusted code |

Rules of thumb: AI clusters run containers on bare metal or VM nodes because they need the GPU driver, RDMA and local storage natively; multi-tenant providers (neoclouds like CoreWeave, Nebius) often wrap customer workloads in VMs or Kata/KubeVirt for tenant isolation while still passing GPUs through; MIG and vGPU partition a physical GPU for sharing (Part 7). Virtualisation internals (VT-x, EPT, virtio, VFIO) are chapters 1.26 and 1.27.

## 10. Observing containers (and the traps)

Containers hide and distort information:

- **Tools inside a container often show host data.** `top` summary lines, `uptime`/load average, `mpstat`, `vmstat`, `free`, `iostat`, and `/proc/cpuinfo`, `/proc/meminfo`, `/proc/stat` report the **host**, because `/proc` and `/sys` statistics are not namespaced. An idle container can show busy disks and CPU that belong to other tenants. Per-process tools (`ps`, `pidstat`) are filtered by the PID namespace. Use the container's **cgroup files** (`cpu.stat`, `memory.current`, `memory.events`, `io.stat`, PSI) for its true usage and limits (chapter 1.18). `lxcfs` can present cgroup-aware `/proc` files.
- **Limits are checked first.** Gregg's strategy: software resource-control limits are hit long before hardware limits, so check cgroup limits and throttling before blaming hardware; most traditional tools (`top`, `iostat`) are blind to them.
- **From the host everything is visible**: container processes appear in the host `ps` with host PIDs; map a PID to a container with `/proc/PID/cgroup` (the container ID is in the path), `crictl ps`/`docker ps`, `nsenter`. There is no container ID in the kernel; BPF tools use the cgroup ID or the UTS nodename.
- **Tracing from inside a container is mostly blocked**: `perf`, `bpftrace`, `strace`(ptrace) need capabilities (`SYS_ADMIN`, `PERFMON`, `BPF`, `SYS_PTRACE`) and access to `/sys/kernel/debug`; container seccomp profiles block `perf_event_open`, `bpf`, `ptrace` by default. Operators trace from the host or use debug containers/ephemeral containers (`kubectl debug`) sharing the target's PID namespace.
- **Noisy neighbours**: contention on shared kernel resources (dentry cache, locks, interrupts, CPU caches) can slow a container without any limit being hit; the diagnosis requires host-side tools.

## 11. GPUs inside containers

Nothing in the namespace/cgroup set knows about GPUs. A GPU appears to a process as **device nodes** (`/dev/nvidia0..N`, `/dev/nvidiactl`, `/dev/nvidia-uvm`, `/dev/nvidia-uvm-tools`, `/dev/nvidia-modeset`; `/dev/nvidia-caps/*` for MIG) plus **user-space libraries** (`libcuda.so`, NVML, and so on) that must match the *host kernel driver version*. To give a container a GPU, a runtime must (1) make the device nodes exist in the container's mount namespace (bind or `mknod`), (2) allow them in the devices cgroup (chapter 1.18), and (3) mount the driver's user-space libraries and binaries (`nvidia-smi`) from the host into the container, since the CUDA *toolkit* libraries can live in the image but the driver library cannot. The **NVIDIA Container Toolkit** (`nvidia-container-runtime`, `nvidia-ctk`, `libnvidia-container`) automates this, historically through an OCI prestart hook and now preferably via **CDI** (Container Device Interface: a declarative spec file listing device nodes, mounts and environment, `nvidia-ctk cdi generate`). Because the driver is in the shared kernel, GPU performance in a container equals bare metal. Chapters in Parts 7 and 8 cover the toolkit, the Kubernetes device plugin, GPU Operator, MIG and time-slicing in depth; flag: verify toolkit commands and CDI behaviour against current NVIDIA documentation.

## 12. Other flavours of "virtual"

- **LXC/LXD/Incus**: system containers that run a whole init and multiple services; more manual (you set up the network, UID mappings), closer to a lightweight VM in spirit. The first Docker versions were built on LXC.
- **Podman**: daemonless, rootless-first, Docker-compatible CLI; containers are children of the invoking process tree (or systemd units via Quadlet).
- **Enroot + Pyxis (Slurm)**: NVIDIA's HPC container path: unprivileged, converts images to a squashfs unpacked into a directory, uses `unshare`-style namespaces without a daemon, and integrates with Slurm via the Pyxis plugin (`srun --container-image`). Apptainer/Singularity is the other HPC runtime. Covered in the Slurm chapters.
- **Language-level environments** (Python `venv`, conda, `nvm`) are not isolation in the kernel sense: they only change search paths (`PATH`, `sys.path`, `VIRTUAL_ENV`) so a program sees different library sets. Sourcing the `activate` script (not executing it) is required because it sets variables in the current shell. Useful, but share nothing with namespaces.
- **Pitfalls of containers** (Ward): wasted storage from big base images and writable layers; you still need a real Linux host and its maintenance; resource limits do not create capacity; ephemeral filesystems require a plan for data and logs; most tooling targets web services, not HPC; careless builds produce bloat and fragility; `latest` tags break reproducibility; image provenance and supply-chain trust must be managed; containers do not make slow startup faster.

## 13. Failure modes and diagnosis

| Symptom | Likely cause | Check / fix |
|---|---|---|
| Pod ignores `SIGTERM`, killed after 30 s, no checkpoint | Shell wrapper or non-handling program is PID 1 | `exec` in entrypoint, `tini`/`--init`, handle `SIGTERM` in the program; raise `terminationGracePeriodSeconds` for large checkpoints |
| Zombie processes pile up, `fork: retry` | PID 1 does not reap; `pids.max` reached | Use an init; check `ps -eo stat \| grep Z`, `cgroup pids.current` |
| `free`/`nproc` show host values, app oversizes thread pools | `/proc` not namespaced | Read cgroup limits; set thread counts explicitly; `lxcfs`; limit-aware runtimes |
| PyTorch "bus error" / DataLoader hangs in container | `/dev/shm` too small (64 MiB default in Docker) | `--shm-size`, `--ipc=host`, memory-backed `emptyDir` |
| Cannot see/mount new host mounts inside container | Mount propagation `private` | Use `HostToContainer` (`rslave`) |
| Node disk full under `/var/lib/containerd` | Large writes to writable layer, stopped containers, unused images, logs | `crictl images`, `du`, move data to volumes, image GC thresholds, log rotation |
| Same image works as root, fails as non-root | UID mapping, file ownership of volumes | `id` inside vs outside, `fsGroup`, user namespace mappings, `/etc/subuid` |
| `Operation not permitted` for `mount`, `ip`, `sysctl` | Missing capability or seccomp/LSM block | Chapter 1.21; do not "fix" with `--privileged` without review |
| `nvidia-smi` fails inside container: "driver/library version mismatch" | Container has own libcuda not matching host driver, or toolkit hook missing | Let the toolkit inject host driver libs; do not bake driver libs in images |
| GPU visible on host, not in container | Device nodes not in container / devices cgroup denies / runtime not configured | `ls -l /dev/nvidia*` in container, runtime class, CDI spec, cgroup driver match (1.18) |
| Pod-to-pod traffic works across nodes but not on the same node (or vice versa) | CNI, bridge netfilter, MTU, hairpin | `nsenter -t PID -n ip route; ss; tcpdump`, check `br_netfilter` sysctls |
| `Cannot create user namespace` | Disabled by policy/sysctl, `user.max_user_namespaces=0` | Distribution policy; AppArmor restriction on Ubuntu |
| Mount leaks onto the host | Shared propagation on root | `--make-rprivate`; verify with `findmnt -o PROPAGATION` |

A generic top-down method for "something is wrong inside a container": (1) can the process start (image pull, rootfs, entrypoint exit code, `crictl ps -a`, `kubectl describe pod`, events)? (2) are limits hit (cgroup `memory.events`, `cpu.stat` throttling, `pids`)? (3) what does the container see (mounts, network, user, devices)? (4) what does the host see for the same PID (`nsenter`, host-side `strace`/`perf`)? (5) what is shared with neighbours (kernel, devices, NIC, disks)?

## 14. Lab: explore and build with namespaces (untested)

Use an Ubuntu 22.04+ VM with root. A full container is assembled in chapter 1.20; this lab builds intuition for each namespace.

1. **Inspect**: `ls -l /proc/$$/ns`, `lsns`. Start `docker run -d --name nsdemo alpine sleep 600` (if Docker is installed), get its PID with `docker inspect -f '{{.State.Pid}}' nsdemo`, then `sudo ls -l /proc/<PID>/ns` and compare inode numbers with the host shell: which are the same, which differ? (With default settings `user` should be the same; `mnt`, `pid`, `net`, `ipc`, `uts`, `cgroup` differ.)
2. **UTS**: `sudo unshare --uts bash -c 'hostname lab-box; hostname'`, then `hostname` in your original shell.
3. **PID**: `sudo unshare --pid --fork --mount-proc bash`; run `ps aux`, `echo $$`; from another terminal find that shell's host PID (`pgrep -f 'unshare --pid'` then `pstree -p`) and note the two PIDs. Try `kill -9 1` inside (nothing happens), then `kill -9 <host PID>` from outside.
4. **PID 1 signals**: in the PID namespace run `sh -c 'sleep 1000'` as PID 1 (`sudo unshare --pid --fork --mount-proc sh -c 'sleep 1000'`), try `kill -TERM` from outside (host PID) vs from a second process inside; then use `exec sleep 1000` vs a script with `trap 'echo got TERM; exit' TERM`.
5. **Mount**: `sudo unshare --mount bash`; `mkdir /tmp/m && mount -t tmpfs tmpfs /tmp/m && touch /tmp/m/x && findmnt /tmp/m`; open another host shell and look: not visible. Repeat with `mount --make-rshared /` first and a bind mount to see propagation (use `findmnt -o TARGET,PROPAGATION`).
6. **Overlay**: run the OverlayFS commands in section 4; inspect `upper/` after writing and deleting; examine a whiteout with `ls -l`.
7. **Network**: follow the `ip netns` + veth recipe in section 5; ping both directions; then add `iptables -t nat -A POSTROUTING -s 10.9.0.0/24 -j MASQUERADE` and `sysctl -w net.ipv4.ip_forward=1` to give the namespace Internet access. Delete the namespace afterwards.
8. **User**: `unshare --user --map-root-user bash`; view `id`, `/proc/self/uid_map`; try to read `/etc/shadow` and to `mount -t tmpfs` (works only if combined with `--mount`).
9. **Enter an existing container's namespaces**: `sudo nsenter -t <PID> -n -p -m ip addr; sudo nsenter -t <PID> -n ss -tlnp`.
10. **IPC**: `ipcmk -M 1024` on the host; `ipcs -m`; then `sudo unshare --ipc ipcs -m`: it is invisible. Compare with `docker run --ipc=host`.
11. **Clean up**: `docker rm -f nsdemo`; remove `/tmp/m` directories, overlay dirs and namespaces.

Record outputs; mark the lab tested only after you have executed it.

## 15. Common mistakes

- Believing a container has its own kernel, or that it is a security boundary equal to a VM.
- Using a shell script as PID 1 without `exec` or an init, losing signals and zombie reaping.
- Trusting `top`, `free`, `/proc/cpuinfo` and `nproc` inside a container.
- Writing datasets, checkpoints or caches into the image layer.
- Deleting files in a later layer and assuming secrets or size are gone.
- Running `--privileged` or `hostPID`/`hostNetwork`/`hostIPC` casually to "make it work".
- Putting two cooperating MPI/NCCL workers in different pods and expecting shared memory.
- Forgetting that user-namespace remapping changes ownership on shared storage.
- Baking driver libraries into images instead of letting the runtime inject them from the host.

## 16. Interview angles

- "What is a container, at the kernel level?" Namespaces + cgroups + rootfs + capabilities/seccomp on a shared kernel; no kernel object.
- "How does `kubectl exec` work?" CRI call to the runtime, which uses `setns` into the container's namespaces and execs.
- "Why does my container ignore SIGTERM?" PID 1 semantics.
- "Explain container networking on a node." Namespace, veth pair, bridge, NAT/CNI; pod shares one network namespace.
- "Containers versus VMs for multi-tenant GPU cloud?" Isolation, GPU passthrough, noisy neighbours, Kata/KubeVirt, MIG.
- "What does OverlayFS do and what is copy-up?"
- "What does `hostNetwork: true` change for NCCL over InfiniBand?"
- "What are user namespaces good for, and why are they hard on HPC storage?"

## 17. Checkpoint questions (30)

1. Is there a "container" object in the Linux kernel? **A:** No; user-space combines namespaces, cgroups, rootfs, capabilities, seccomp and LSMs.
2. What is the difference between what namespaces and cgroups control? **A:** Namespaces limit what a process can see; cgroups limit what it can use.
3. Name the eight namespace types. **A:** mnt, pid, net, uts, ipc, user, cgroup, time.
4. What are the three namespace-related system calls? **A:** `clone` (create with new process), `unshare` (calling process leaves), `setns` (join existing).
5. How does `docker exec` relate to namespaces? **A:** It `setns`-joins the container's namespaces and execs a program.
6. How do you see which namespaces a process is in? **A:** `ls -l /proc/PID/ns`, `lsns -p PID`.
7. What keeps a namespace alive with no processes? **A:** An open file descriptor or a bind mount of `/proc/PID/ns/*` (e.g. `/run/netns/name`).
8. What is special about PID 1 in a PID namespace? **A:** No default signal actions for in-namespace signals, reaps orphans, and its exit kills the whole namespace.
9. Why does `unshare --pid` need `--fork`? **A:** The calling process does not move; only its children enter the new PID namespace.
10. Why must `/proc` be remounted in a new PID namespace? **A:** Otherwise it still reflects the host's PID view.
11. How do you make a container honour SIGTERM correctly? **A:** `exec` the real program or use an init; handle the signal.
12. What does a new mount namespace start with? **A:** A copy of the parent's mount table.
13. What is mount propagation, and why do runtimes set it to private/slave? **A:** Events flow between peer mounts; avoid leaking container mounts to the host.
14. How do `chroot` and `pivot_root` differ? **A:** `chroot` only changes the root directory and is escapable; `pivot_root` swaps the root mount in a mount namespace and detaches the old root.
15. What are OverlayFS's `lowerdir`, `upperdir`, `workdir`? **A:** Read-only layers, read-write layer, scratch directory for atomic ops.
16. What is copy-up and why can it hurt AI jobs? **A:** First write copies the whole file to the upper layer; big files cause I/O spikes and disk exhaustion.
17. What is a whiteout? **A:** A 0/0 character device in the upper layer that hides a lower file.
18. Why doesn't deleting a file in a later Dockerfile layer shrink the image? **A:** Lower layers retain the data; only a whiteout is added.
19. What does a new network namespace contain? **A:** Only a down loopback interface.
20. How are containers connected to the outside network in the default Docker setup? **A:** veth pair to a bridge, NAT via iptables.
21. What does a Kubernetes pod share? **A:** Network, IPC and UTS namespaces (and optionally PID), via the pause container; mount namespaces are per container.
22. What does `hostNetwork: true` do? **A:** Runs the pod in the host's network namespace; no isolation.
23. What is a user namespace and how does mapping work? **A:** Separate UID/GID space with maps in `uid_map`/`gid_map`; root inside maps to an unprivileged ID outside.
24. Why are user namespaces awkward on HPC clusters? **A:** Shared-filesystem ownership and quotas depend on real UIDs.
25. Why can two pods not share SysV shared memory? **A:** Different IPC namespaces.
26. Why does PyTorch crash with a bus error in Docker and how do you fix it? **A:** `/dev/shm` defaults to 64 MiB; raise `--shm-size` or share host IPC/tmpfs.
27. Why do `top`/`free` inside a container show host numbers? **A:** `/proc` and `/sys` statistics are not namespaced; use cgroup files.
28. Why is tracing inside a container usually blocked? **A:** Needs capabilities and syscalls (`perf_event_open`, `bpf`, `ptrace`) that default profiles deny.
29. What three things must a runtime do to give a container a GPU? **A:** Provide device nodes, allow them in the devices cgroup, mount matching driver libraries.
30. Containers versus MicroVMs: one key difference? **A:** MicroVMs have their own guest kernel and hardware isolation with small overhead; containers share the host kernel.

## 18. Sources and review notes

**Written in original words.** Principal sources:

- Brian Ward, *How Linux Works*, 3rd ed., chapter 17 (virtualization): hypervisors, containers, Docker, overlay filesystems, networking, process models, LXC, Kubernetes, pitfalls, runtime-based virtualization.
- Brendan Gregg, *Systems Performance*, 2nd ed., chapter 11 (cloud computing): OS virtualization (namespaces, cgroups, overhead, resource controls, observability, tool container-awareness), lightweight virtualization, comparisons.
- The project's own `nvidia-devops` notes: Volume 1 chapter 4 (namespaces, `unshare` lab, OverlayFS mechanics, signals and PID 1), migrated and rewritten.
- Manual pages `namespaces(7)`, `pid_namespaces(7)`, `user_namespaces(7)`, `mount_namespaces(7)`, `network_namespaces(7)`, `unshare(1)`, `nsenter(1)`, `ip-netns(8)`, and the OCI runtime spec, from general knowledge; verify details on the target kernel.

**Hardware-virtualisation parts of both chapters** (hypervisor types, CPU modes, VT-x, EPT, virtio, instance types, multitenancy) are routed to chapters 1.26 and 1.27; the cloud-architecture material (instance types, capacity planning, orchestration) to Part 11 and the Kubernetes chapters.

**Flagged for verification before publishing:**

- Linux version numbers for time namespace (5.6), unprivileged overlay mounts (5.11), ID-mapped mounts (5.12).
- Kubernetes user-namespace support status and `hostUsers` behaviour per version.
- Ubuntu restrictions on unprivileged user namespaces; `kernel.unprivileged_userns_clone` availability.
- NVIDIA Container Toolkit / CDI commands; RDMA namespace modes.
- Docker defaults (`/dev/shm` size) and containerd paths.
- All labs are **untested** and need a real run.
