---
id: "c06-13"
title: "6.13 Containers on Slurm: enroot and pyxis"
sidebar_label: "6.13 Containers on Slurm: enroot and pyxis"
sidebar_position: 13
description: "Running containerised GPU jobs under Slurm with NVIDIA enroot and the pyxis SPANK plugin: how they differ from Docker, image import and squashfs, the srun --container-* options, mounts, hooks for GPUs and InfiniBand, registry credentials, caching, PMIx and PyTorch integration, security model, and operating image distribution at scale"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.13 Containers on Slurm: enroot and pyxis

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Linux GPU nodes with Slurm, enroot and pyxis |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Read from the source repositories (NVIDIA/enroot commit `0bb3810`, 2026-10-21, docs and default configuration; NVIDIA/pyxis commit `1075199`, 2026-05-11, README and option text). Nothing was executed: enroot needs Linux user namespaces and pyxis needs a Slurm build, neither available here. Labs **untested** |

## Why this matters for AI infrastructure

Almost every serious GPU cluster runs AI jobs from container images (NGC PyTorch/NeMo, vendor stacks, team images), because the framework, CUDA libraries, NCCL and Python packages must match each other and cannot be installed on every node by hand. On Slurm clusters NVIDIA's pair **enroot** (an unprivileged container runtime) and **pyxis** (a Slurm plugin exposing it through `srun`) is the reference solution on DGX SuperPOD-style systems and many neoclouds. Docker daemons and root-owned containers are poor fits for shared HPC nodes; enroot and pyxis give containerised steps with the same Slurm semantics (cgroups, accounting, signals, binding) as bare-metal ones. Understanding them is expected for an AI-infrastructure role.

## Prerequisites and outcomes

Needs 6.6 (software strategy), 6.10 to 6.12, and container basics (Part 5.1 to 5.4). After this chapter you can:

- Explain why Docker is not used on shared compute nodes and what enroot does instead.
- Use `srun`/`sbatch` with `--container-image`, `--container-mounts`, `--container-workdir`, `--container-name`, `--container-save`, and other pyxis options.
- Describe the image flow: registry, import, squashfs, container root, caching, and where each lives.
- Explain the hooks that give containers GPUs, InfiniBand and Slurm/PMIx/PyTorch variables, and the standard security posture.
- Authenticate to registries and use mirrors/caches; plan image distribution for thousands of nodes.
- Install and configure enroot and pyxis at a high level and troubleshoot common failures.

## 1. Why not Docker on compute nodes

| Concern | Docker daemon model | enroot/pyxis |
|---|---|---|
| Privilege | Root daemon; `docker` group is effectively root | Unprivileged: user namespaces and `chroot`-like environment; runs as the user |
| Scheduler integration | Containers are children of the daemon, outside Slurm's cgroup and accounting | The container process is the Slurm task: cgroups, signals, accounting, GPU isolation apply |
| Isolation goals | Strong isolation between containers | Intentionally minimal: same PID/network namespace as host by default, to preserve HPC behaviour (RDMA, shared memory) |
| Image storage | Layered storage per node, daemon-managed | Converted to a squashfs/rootfs; can live on shared storage; cache per user |
| Multi-node MPI/NCCL | Needs network plumbing | Works with the host network and IB devices directly |

The enroot README describes itself as a "simple, yet powerful tool to turn traditional container/OS images into unprivileged sandboxes", close to a fancy `chroot`. Its design drops features HPC does not need (daemons, network isolation, image layering at runtime) and keeps what it does: importing Docker/OCI images, running them unprivileged with host GPU and IB integration. Other HPC options (Apptainer/Singularity) are in 6.29.

## 2. enroot

### Workflow

```bash
enroot import docker://nvcr.io#nvidia/pytorch:24.07-py3     # pull layers, build a squashfs: nvidia+pytorch+24.07-py3.sqsh
enroot create --name pt nvidia+pytorch+24.07-py3.sqsh        # unpack into a container root under ENROOT_DATA_PATH
enroot list
enroot start --rw pt python -c "import torch; print(torch.cuda.is_available())"
enroot export --output pt-modified.sqsh pt                   # save changes back to an image
enroot remove pt
```

(Commands as listed in the enroot usage documentation: `batch`, `bundle`, `create`, `exec`, `export`, `import`, `list`, `remove`, `start`, `version`.) Note the URI form `docker://REGISTRY#IMAGE:TAG`: **`#` separates registry from image** because `/` and `:` are ambiguous; for NGC it is `nvcr.io#nvidia/pytorch:TAG`. `enroot start --root --rw` gives a writable container where the user appears as root (a user-namespace mapping, no real privilege), used to install packages and then `export`.

The result of `import` is a **squashfs** image (compressed read-only filesystem; default options `-comp lzo -noD -exit-on-error` in the sample config, with `ENROOT_MAX_PROCESSORS` controlling compression threads). `create` unpacks it to a directory tree (the container root) in per-user storage. Squashfs images are single files, so they distribute well (one large file instead of thousands) and can be placed on shared or node-local storage.

### Paths and configuration

From `configuration.md`: configuration comes from `enroot.conf` (default `/etc/enroot`) or environment variables, with environment taking precedence, plus `enroot.conf.d/*.conf`. Standard paths (defaults):

| Setting | Default | Meaning |
|---|---|---|
| `ENROOT_RUNTIME_PATH` | `${XDG_RUNTIME_DIR}/enroot` | Working directory at runtime (must be local, writable) |
| `ENROOT_CONFIG_PATH` | `${XDG_CONFIG_HOME}/enroot` | User configuration |
| `ENROOT_CACHE_PATH` | `${XDG_CACHE_HOME}/enroot` | Layer cache and credentials |
| `ENROOT_DATA_PATH` | `${XDG_DATA_HOME}/enroot` | User container storage (unpacked roots) |
| `ENROOT_TEMP_PATH` | `${TMPDIR}` | Temporary files (large during import) |
| `ENROOT_SQUASH_OPTIONS`, `ENROOT_MAX_PROCESSORS`, `ENROOT_ROOTFS_WRITABLE`, `ENROOT_REMAP_ROOT`, `ENROOT_TRANSFER_RETRIES` | see sample config | Compression, threads, default writability, root remapping, retries |

On clusters set these to **node-local fast storage** (NVMe, `/raid` or `/tmp`) for runtime and data paths, and to an appropriate shared location for caches only if you accept the metadata load; home directories on NFS are a poor default (unpacking and running from them is slow and hammers the server).

### Hooks, mounts, environment

Containers are customised by directories under `ENROOT_SYSCONF_PATH` (system) and `ENROOT_CONFIG_PATH` (user): `environ.d/*.env` (environment variables exported in the container), `mounts.d/*.fstab` (mounts), `hooks.d/*.sh` (pre-start bash scripts run with full capabilities before the container switches to its final root). Hooks see `ENROOT_PID`, `ENROOT_ROOTFS`, `ENROOT_MOUNTS`, `ENROOT_ENVIRON`. The standard hooks (`standard-hooks.md`, `conf/hooks`):

| Hook | Role |
|---|---|
| `10-cgroups.sh` | Mount cgroup controllers in a new cgroup namespace (always on) |
| `10-devices.sh` | Restrict `/dev` to a minimal set (`ENROOT_RESTRICT_DEV`, default `no`) |
| `10-home.sh` | Mount the user's home (`ENROOT_MOUNT_HOME`, default `no`) |
| `10-shadow.sh` | Add entries for the current user/group to `/etc/passwd` and `/etc/group`; create the home directory (always on) |
| `10-localtime.sh`, `10-aptfix.sh` | Time zone; apt compatibility |
| **`98-nvidia.sh`** | GPU support via `libnvidia-container`; controlled by `NVIDIA_VISIBLE_DEVICES`, `NVIDIA_DRIVER_CAPABILITIES`, etc. (the nvidia-container-runtime variables). It injects the host driver libraries and device nodes matching the host driver version |
| **`99-mellanox.sh`** | InfiniBand/RDMA: injects MOFED from the host, controlled by `MELLANOX_VISIBLE_DEVICES` |
| `extra/50-slurm-pmi.sh` | Passes `SLURM_*` and `PMIX_*` variables and PMIx sockets into the container for MPI launches |
| `extra/50-slurm-pytorch.sh` | Sets PyTorch distributed variables from Slurm |
| `extra/50-sharp.sh`, `50-mig-config.sh` | SHARP and MIG support |

(The `extra` hooks are provided but not enabled by default; they are copied into `hooks.d` by the site, usually by the DGX/cluster software image.) The hooks explain two key behaviours: **GPU libraries inside the container come from the host driver**, not the image (the image supplies CUDA user-space libraries, the hook supplies `libcuda`, so the image's CUDA version must be compatible with the host driver, Part 10); and **IB/RDMA works because the hook injects host MOFED** into the container. If `nvidia-smi` works in the container but NCCL runs on sockets, check the Mellanox hook and device visibility.

## 3. pyxis

Pyxis is a **SPANK plugin** (a Slurm extension point for adding command-line options and running code at task launch): it adds options to `srun` and `sbatch`, imports/creates the container using enroot on the compute node, and runs each task inside it, so the container *is* the Slurm task. Requirements per the README: enroot 3.1.0 or later, and pyxis must be built against the Slurm version in use (since Slurm 21.08); it is installed on compute nodes (and where `srun` is used) and enabled with a `plugstack.conf` entry, e.g. symlinking `pyxis.conf` into `/etc/slurm/plugstack.conf.d/` and restarting slurmd.

Options (from the pyxis README text):

| Option | Meaning |
|---|---|
| `--container-image=[USER@][REGISTRY#]IMAGE[:TAG]` or `PATH` | Image to use: an enroot/Docker URI or a path to a squashfs file on the host filesystem |
| `--container-mounts=SRC:DST[:FLAGS][,...]` | Bind mounts; flags joined with `+` (e.g. `ro+rprivate`) |
| `--container-workdir=PATH` | Working directory |
| `--container-name=NAME` | Name to save/load the container. **Unnamed containers are removed when the task completes; named ones persist, and an existing named container is reused with the import skipped** |
| `--container-save=PATH` | Save the container state to a squashfs file |
| `--container-mount-home` / `--no-container-mount-home` | Bind mount the user's home (system enroot settings may already mount it) |
| `--container-remap-root` / `--no-container-remap-root` | Appear as root inside (does not grant elevated permissions) |
| `--container-entrypoint` / `--no-container-entrypoint`, `--container-entrypoint-log` | Run or skip the image's entrypoint; show its output |
| `--container-writable` / `--container-readonly` | Writability of the container filesystem |
| `--container-env=NAME[,...]` | Variables whose host values override the image's (set before the entrypoint). By default host variables are set after the entrypoint but **do not override values in the image** |
| `--container-unshare=NS[,...]` | Create new namespaces: `net`, `ipc`, `uts` |

Examples from the README:

```console
$ srun --container-image=almalinux:9 grep PRETTY /etc/os-release
pyxis: importing docker image: almalinux:9
pyxis: imported docker image: almalinux:9
PRETTY_NAME="AlmaLinux 9.7 (Moss Jungle Cat)"

$ srun --container-image=almalinux:9 --container-mounts=/etc/os-release:/host/os-release grep PRETTY /host/os-release
```

In `sbatch` the option can be a directive, with the `#` escaped because `#` starts a comment: `#SBATCH --container-image nvcr.io\#nvidia/pytorch:21.12-py3`.

### A training job

```bash
#!/bin/bash
#SBATCH --nodes=4 --ntasks-per-node=8 --gpus-per-node=8 --cpus-per-gpu=12 --exclusive --time=12:00:00
IMG=/shared/images/nvidia+pytorch+24.07-py3.sqsh        # pre-imported squashfs on fast shared storage
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n1)
export MASTER_PORT=$((10000 + SLURM_JOB_ID % 20000))
srun --kill-on-bad-exit=1 --cpu-bind=cores --gpu-bind=closest \
     --container-image="$IMG" \
     --container-mounts=/data:/data:ro,/scratch/$USER:/scratch,$PWD:/workspace \
     --container-workdir=/workspace \
     python train.py
```

Key points: the container starts for every task on every node, so startup cost multiplies; use a **squashfs path** (no registry pull at job time); mount datasets and output directories explicitly; keep `/dev/shm` large enough for data-loader workers (container shm is the host's); Slurm binding and GPU isolation apply because enroot runs inside the step; environment and the `SLURM_*` and `PMIX_*` variables enter the container through the Slurm hooks (check `env | grep -E "SLURM|PMIX"` inside).

### Multi-node MPI/NCCL in containers

Use `srun --mpi=pmix` with a container whose MPI is PMIx-aware and compatible with the host's PMIx/Slurm (the pyxis README notes support for PMI2 and PMIx "requires Slurm support"; the `50-slurm-pmi.sh` hook forwards the PMIx variables and socket). NGC images ship HPC-X with PMIx support. A mismatch between the container's PMIx and the host's causes launch failures at `MPI_Init` (6.4 section 11). NCCL inside the container uses the injected host IB libraries and devices.

## 4. Images: sources, caching, distribution

- **Sources**: NGC (`nvcr.io#nvidia/...`, requires an API key for some images), Docker Hub, GitHub Container Registry, private registries. Build images from NGC bases with a normal Docker/Podman/Buildah build **outside** the cluster, push to a registry, then import into squashfs.
- **Credentials**: enroot reads registry credentials from `$ENROOT_CONFIG_PATH/.credentials` in **netrc format**, e.g. `machine nvcr.io login $oauthtoken password <NGC API key>` (the user name `$oauthtoken` is the NGC convention). Protect the file (mode 600). Do not put keys in job scripts.
- **Cache**: layer cache in `ENROOT_CACHE_PATH` makes repeat imports fast and layer sharing efficient. On thousands of nodes a registry pull at job start is a thundering herd: you will saturate the registry or the uplink and get rate limits.
- **Preferred pattern at scale**: import once, centrally, to a squashfs on shared parallel storage or an image distribution service; jobs use `--container-image=/path/to/image.sqsh`. Squashfs is one big read-mostly file: good for Lustre/GPFS/VAST/WEKA caching, and for node-local copies (pre-stage with `sbcast`/`pdcp`/a prolog to NVMe before large jobs). Version images by digest or dated tag; never use `:latest` for production runs.
- **Local registry mirror/pull-through cache** (Harbor, Artifactory, a registry:2 mirror) for NGC and Docker Hub to avoid external rate limits and for supply-chain control (scan, sign; Part 18 and 5.22).
- **Storage budget**: PyTorch NGC images are many gigabytes; unpacked roots also consume `ENROOT_DATA_PATH`; unnamed pyxis containers are cleaned up after tasks, named ones need housekeeping.
- **Reproducibility**: record the image digest in the job's accounting comment or log.

## 5. Security and policy

- Enroot runs as the invoking user in user namespaces; the container "root" is the user (remapping only). It does not grant privilege escalation by itself, but the hooks run with capabilities during setup, so hook scripts and enroot configuration are privileged, security-sensitive files (root-owned).
- Namespace choices favour HPC: by default no network namespace, so the container shares the host network. `--container-unshare=net` is available but breaks RDMA unless you set it up.
- Kernel prerequisites (from `requirements.md`): Linux >= 3.10 with `CONFIG_NAMESPACES`, `CONFIG_USER_NS`, `CONFIG_SECCOMP_FILTER`, and `CONFIG_OVERLAY_FS` to import Docker images; `enroot-check` verifies. Some distributions restrict unprivileged user namespaces (AppArmor profile in recent Ubuntu releases): the repository ships an `apparmor.profile`; you may need to allow enroot.
- Image trust: users can run arbitrary images, including ones that exfiltrate data from mounted paths. Mount only what is needed (`:ro` for datasets), restrict registries via mirror, scan images, and treat user-supplied images as untrusted code with the user's file permissions (which is what they are anyway).
- Writable containers (`--container-writable`, `enroot start --rw`) change only the user's own copy; they are not shared unless exported.

## 6a. Other HPC container runtimes: Singularity and Charliecloud

The SCL book's container chapter covers two alternatives that you will meet on academic and national-lab systems (6.29 compares them in depth):

- **Singularity / Apptainer**: a single-file image (SIF, squashfs inside) executed by a setuid or user-namespace runtime; the user inside the container is the same user as outside, host filesystems are bind-mounted by default, GPUs via `--nv`. Slurm integration is by running `apptainer exec` inside `srun` (no plugin needed) or through its own SPANK/OCI support. Strengths: mature in HPC, signed images, no daemon. Compared with enroot/pyxis it has no first-class Slurm option set, so scripts are more verbose, but it is widely supported by site-installed software stacks.
- **Charliecloud**: a minimal, fully unprivileged runtime built on user namespaces; images are unpacked directory trees or squashfs; focused on simplicity and security audits (small code base). Similar spirit to enroot; used mostly at a few labs.

On NVIDIA-centric AI clusters enroot+pyxis is the default because of NGC image handling, hooks for GPU/IB/PMIx and the `--container-*` UX; Apptainer is the common choice where the same cluster serves classic HPC users.

## 6. Operating it

| Task | Practice |
|---|---|
| Install | Package or `make install` on all compute nodes; set `enroot.conf` (paths on local NVMe), hooks, `plugstack.conf.d/pyxis.conf`; restart slurmd |
| Verify | `enroot version`, `enroot-check`, `srun --container-image=ubuntu:24.04 cat /etc/os-release`, `srun --gres=gpu:1 --container-image=<cuda image> nvidia-smi` |
| Upgrade | Rebuild pyxis whenever Slurm is upgraded (the plugin links against Slurm); roll out enroot and pyxis with the node image |
| Monitor | Import failure rates, time-to-first-output, registry bandwidth, disk use of `ENROOT_DATA_PATH` and cache, `/dev/shm` |
| Housekeeping | Prune named containers and cache older than N days (epilog or cron), clean orphaned runtime dirs after node crashes |
| Support | A short doc: how to get images in, naming, mounts, shm, known gotchas, example scripts |

## 7. Troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| `pyxis: unrecognized option --container-image` | Plugin not loaded in `srun`/slurmd, `plugstack.conf` missing, built against the wrong Slurm | `scontrol show config \| grep -i plugstack`, slurmd log, `srun --help \| grep container` |
| Import is slow or fails mid-job | Registry rate limit/auth, no credentials, many nodes pulling at once, `ENROOT_TEMP_PATH` too small | Use squashfs path; check `.credentials` format; local mirror |
| `nvidia-smi: command not found` or no GPU in container | `NVIDIA_VISIBLE_DEVICES` unset by image/hook, `98-nvidia.sh` not installed, driver library mismatch, GPUs not allocated | Hook list, `enroot start` env, Slurm `--gres` |
| CUDA error: driver version insufficient | Image CUDA newer than host driver supports | Update driver or use older image (Part 10) |
| NCCL falls back to sockets inside container | Mellanox hook missing or IB devices not visible (`MELLANOX_VISIBLE_DEVICES`), `NCCL_IB_HCA` wrong | `ls /dev/infiniband`, NCCL INFO (6.12) |
| MPI launch fails in container | PMIx mismatch between host and container | `srun --mpi=list`, MPI/PMIx versions in the image |
| `Operation not permitted` on mount/namespace | Unprivileged user namespaces disabled or AppArmor restriction | `sysctl kernel.unprivileged_userns_clone`, `kernel.apparmor_restrict_unprivileged_userns`, `enroot-check` |
| Out of space | Data path on small `/tmp`; many named containers | `df`, `enroot list`, clean-up |
| Job's environment variables missing in container | Pyxis defaults: host variables do not override image values | `--container-env=NAME` |
| Slow startup of 512 ranks | Each task creates the container; shared FS metadata storm | Squashfs on fast storage, local copy, `--container-name` reuse within a node |

## 8. Lab (untested)

1. Install enroot on a Linux VM; run `enroot-check`; `enroot import docker://ubuntu:24.04`, create and start it; inspect hooks directory.
2. Configure NGC credentials; import `nvcr.io#nvidia/pytorch:<tag>`; record time and size of the squashfs and the unpacked container.
3. Install pyxis on a test Slurm; run the README examples; test `--container-mounts`, `--container-name` reuse, `--container-save`.
4. GPU node: run `nvidia-smi` and a CUDA sample in a container; break `98-nvidia.sh` (rename) and observe.
5. Two nodes: run the 6.12 DDP or an `nccl-tests` container with `srun --mpi=pmix`; compare NCCL transport with and without the Mellanox hook.
6. Scale test: launch the same job from the registry URI vs a squashfs path on shared storage on N nodes; plot start latency.
7. Write the site doc for image workflow and a housekeeping script.

## 9. Interview angles

- Why enroot and pyxis rather than Docker on a Slurm cluster?
- How does a container get GPUs and InfiniBand without privilege?
- What does pyxis add to `srun`? Why is it a SPANK plugin?
- How would you distribute a 20 GB image to 1,000 nodes for a job launch?
- A container job runs but NCCL uses TCP. What do you check?
- `--container-name` versus unnamed containers: when each?
- What are the security implications of letting users run arbitrary images?
- Why must pyxis be rebuilt after a Slurm upgrade?
- Compare enroot/pyxis with Apptainer and with Kubernetes pods for training.

## 10. Checkpoint questions (25)

1. Name three reasons Docker daemons are unsuited to shared compute nodes.
2. What is enroot, in one sentence?
3. What does `enroot import` produce?
4. What does `#` mean in `docker://nvcr.io#nvidia/pytorch:TAG`?
5. Which paths hold cache, data and runtime state?
6. What does `98-nvidia.sh` do and where do the GPU libraries come from?
7. What does `99-mellanox.sh` do?
8. What are enroot hooks, mounts and environ directories?
9. What is a SPANK plugin?
10. List five pyxis options.
11. What happens to unnamed containers after the task?
12. How do you escape `#` in `#SBATCH --container-image`?
13. What does `--container-env` change versus the default?
14. Where are registry credentials stored and in which format?
15. Why avoid pulling from a registry at job start on many nodes?
16. How would you pre-stage images?
17. What kernel features does enroot need?
18. Why is network namespace isolation off by default?
19. What do the `50-slurm-pmi.sh` and `50-slurm-pytorch.sh` hooks do?
20. What breaks when the container's PMIx mismatches the host's?
21. What does a driver/CUDA mismatch look like?
22. How do you keep images reproducible?
23. What housekeeping do named containers require?
24. When must pyxis be rebuilt?
25. How does container start cost scale with ranks?

## 11. Sources and review notes

- enroot: repository documentation (`usage.md`, `configuration.md`, `standard-hooks.md`, `requirements.md`, `image-format.md`) and the sample `conf/` hooks (commit `0bb3810`). pyxis: README and option help (commit `1075199`). The pyxis wiki (installation, setup, usage) was not read. Prose is my own.
- HPC container context and operations: *Supercomputers for Linux SysAdmins* (software environments, ch. 21) and the NVIDIA-DevOps volume notes on Slurm and containers; Apptainer alternatives in 6.29.
- Unverified: exact `98-nvidia.sh` behaviour on your driver version, which `extra/` hooks your distribution enables by default, current Ubuntu AppArmor settings and sysctl names, NGC credential conventions, image sizes and timing figures (none measured).
