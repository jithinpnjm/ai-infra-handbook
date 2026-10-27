---
id: "c06-12"
title: "6.12 Multi-node training on Slurm: PMIx, torchrun, NCCL environment, binding"
sidebar_label: "6.12 Multi-node training on Slurm: PMIx, torchrun, NCCL environment, binding"
sidebar_position: 12
description: "Launching distributed training under Slurm: control plane versus data plane, srun with one task per GPU versus torchrun per node, rendezvous from Slurm variables (tested with a fake-srun DDP harness), PMIx for MPI, NCCL environment variables, CPU/GPU/NIC binding, FSDP/DeepSpeed/Megatron launch patterns, and diagnosing hangs"
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 6.12 Multi-node training on Slurm: PMIx, torchrun, NCCL environment, binding

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Slurm cluster with a fabric; the harness runs on a laptop (CPU, gloo) |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. The Slurm-to-PyTorch glue was **run**: `code/part06/fake_srun.py` started 4 local processes with the `SLURM_*` variables a real `srun` sets, and `ddp_toy.py` (PyTorch 2.14.1, gloo backend, CPU) completed an all-reduce, a DDP step with identical weights on all ranks, a rank-0 checkpoint and a resumed second run. NCCL variable descriptions were read from `docs/userguide/source/env.rst` in a shallow clone of NVIDIA/nccl (commit `3e46c08`, 2026-10-08). Real multi-node GPU runs are **untested** |

## Why this matters for AI infrastructure

This is the chapter where scheduler, fabric and framework meet. Most "my 64-GPU job hangs at start", "scaling is bad", "one rank crashed and the rest sat there for six hours" tickets are launch-layer problems: wrong rendezvous address, ranks on the wrong NUMA node, NCCL choosing the management NIC, a missing `-K`, mismatched library versions. An engineer who can read a launch script and predict its failure modes is worth a great deal on an AI cluster.

## Prerequisites and outcomes

Needs 6.4, 6.10, 6.11, and Part 10/12 basics (NCCL, fabric). After this chapter you can:

- Separate control plane (Slurm, PMIx, rendezvous) from data plane (NCCL over NVLink/IB/RoCE).
- Launch one task per GPU with `srun`, or one `torchrun` per node, and choose between them.
- Derive `RANK`, `LOCAL_RANK`, `WORLD_SIZE`, `MASTER_ADDR`, `MASTER_PORT` from Slurm and test that glue without a cluster.
- Set NCCL environment variables deliberately (interfaces, HCAs, GDR, debug) and know which are risky.
- Bind CPUs, GPUs and NICs correctly; run FSDP, DeepSpeed and Megatron-LM style jobs.
- Triage hangs, slow collectives and partial failures.

## 1. Layers

```mermaid
flowchart TB
  S[Slurm: allocation, cgroups, srun steps] --> L[Launcher: srun or torchrun]
  L --> R[Rendezvous: MASTER_ADDR/PORT, c10d store or PMIx]
  R --> F[Framework: torch.distributed, DDP/FSDP, DeepSpeed, Megatron]
  F --> N[NCCL: topology detection, rings/trees]
  N --> NV[NVLink / NVSwitch in node]
  N --> IB[GPUDirect RDMA over IB or RoCE between nodes]
```

Slurm decides *where* processes run and constrains them. The launcher starts them. Rendezvous lets ranks find each other: for MPI programs PMIx performs wire-up through the Slurm step daemons; for PyTorch the `env://` method uses a TCP store at `MASTER_ADDR:MASTER_PORT` which also distributes NCCL's unique id. After that NCCL talks directly over the fabric; Slurm and PMIx are out of the data path. PyTorch does not use PMIx; it needs the four variables below.

## 2. Two launch styles

**A. `srun`, one task per GPU** (Slurm starts every rank):

```bash
#SBATCH --nodes=4 --ntasks-per-node=8 --gpus-per-node=8 --cpus-per-gpu=12 --exclusive
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n1)
export MASTER_PORT=$((10000 + SLURM_JOB_ID % 20000))
srun --kill-on-bad-exit=1 --cpu-bind=cores --gpu-bind=closest python train.py   # train.py derives RANK etc. from SLURM_*
```

Pros: Slurm controls binding, cgroups, accounting per step, signals and failure handling; no per-node launcher process. Cons: the training script must read `SLURM_PROCID`, `SLURM_LOCALID`, `SLURM_NTASKS` (or you wrap it).

**B. `torchrun`, one task per node** (torchrun starts the 8 local ranks):

```bash
#SBATCH --nodes=4 --ntasks-per-node=1 --gpus-per-node=8 --cpus-per-task=96 --exclusive
srun torchrun --nnodes=$SLURM_NNODES --nproc-per-node=8 \
  --rdzv-backend=c10d --rdzv-endpoint=$MASTER_ADDR:29500 --rdzv-id=$SLURM_JOB_ID train.py
```

Pros: torchrun provides elastic features (restart on failure, rendezvous), sets all variables, and the script is launcher-agnostic. Cons: Slurm sees one task per node, so per-rank binding and GPU isolation are coarser; process monitoring is torchrun's; `--cpus-per-task` must cover all 8 ranks.

Choice: **srun-per-GPU** for tightly controlled bare-metal clusters with strong binding requirements; **torchrun** when portability (laptop, Kubernetes, Slurm) or elasticity matters. Both appear in NVIDIA reference setups. Frameworks add their own: DeepSpeed's `deepspeed` launcher (pdsh/mpirun/Slurm runners), Megatron-LM scripts built on `torchrun`, NeMo launchers that generate `sbatch` for you.

## 3. The glue, tested

`code/part06/slurm_dist_init.py` turns Slurm variables into the rendezvous set:

```python
def dist_env(env=None, port_base=10000):
    e = os.environ if env is None else env
    job = int(e.get("SLURM_JOB_ID", "0"))
    return {
        "RANK": e["SLURM_PROCID"], "LOCAL_RANK": e["SLURM_LOCALID"], "WORLD_SIZE": e["SLURM_NTASKS"],
        "MASTER_ADDR": e.get("MASTER_ADDR") or first_host(e["SLURM_JOB_NODELIST"]),
        "MASTER_PORT": e.get("MASTER_PORT") or str(port_base + job % 20000),
    }
```

`first_host` calls `scontrol show hostnames` and falls back to a local hostlist expander (unit-checked: `gpu[01-03,07],cpu1,x[9-10]` expands correctly). `ddp_toy.py` calls it, initialises `torch.distributed` with `env://`, checks an all-reduce (`world*(world+1)/2`), runs one DDP step with different data per rank, verifies the resulting weights are identical on all ranks (gradient averaging works), saves a checkpoint from rank 0 and resumes from it. `fake_srun.py 2 2 python ddp_toy.py` started 4 processes with `SLURM_PROCID=0..3`, `SLURM_LOCALID`, `SLURM_NODEID`, `SLURM_NTASKS=4`, `SLURM_JOB_NODELIST=node[01-02]`. Result:

```text
rank 0/4 local=0 master=127.0.0.1:14242 allreduce_ok weights_identical=True start_step=0
rank 1/4 local=1 ... weights_identical=True start_step=0
rank 2/4 local=0 ... start_step=0
rank 3/4 local=1 ... start_step=0
(second run) ... start_step=1   # resumed from the rank-0 checkpoint
```

The port came out as 14242 from job id 4242, as the formula says. `MASTER_ADDR` was overridden to 127.0.0.1 because `node01` does not resolve on a laptop. On a GPU cluster use `BACKEND=nccl`, move tensors to `cuda:LOCAL_RANK` (with `ConstrainDevices` each task sees its GPUs renumbered from 0, 6.10) and pass `device_ids=[local_rank]`. This is a **logic test of the glue**, not of fabric behaviour.

An environment lesson from this same session: installing PyTorch via pip into a conda environment that already provided LLVM's OpenMP produced `OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized` and an abort. That is exactly the "two OpenMP runtimes in one process" hazard from 6.5. The unsafe workaround `KMP_DUPLICATE_LIB_OK=TRUE` exists; the right fix is one environment with one runtime (I used a clean venv).

## 4. Rendezvous gotchas

- `MASTER_ADDR` must be resolvable and reachable from every node on the interface you intend; the first hostname of the nodelist is usually the management name. If the management and fabric networks differ, torch's TCP store uses the one `MASTER_ADDR` resolves to, which is fine, but NCCL's bootstrap uses `NCCL_SOCKET_IFNAME` (below).
- Port collisions on shared nodes: derive from the job ID or ask the site. Firewalls must allow the port range between compute nodes.
- With torchrun's c10d rendezvous the endpoint host must be reachable; `--rdzv-id` must be unique per job.
- Only one job should use a given port on a given node at a time; `--exclusive` helps.
- If ranks start at different times (slow image pull, slow module load) the rendezvous timeout may fire; increase it, and fix the slow start.

## 5. NCCL environment variables

From the NCCL user guide (`env.rst`, verified in the clone): 

| Variable | Meaning and notes |
|---|---|
| `NCCL_DEBUG` | `VERSION`, `WARN`, `INFO` (and more detail via subsystems); first tool for any hang. `NCCL_DEBUG_SUBSYS` selects subsystems (`INIT,NET,GRAPH,ENV`...); `NCCL_DEBUG_FILE=file.%h.%p` writes per host/process |
| `NCCL_SOCKET_IFNAME` | Interfaces for NCCL's bootstrap and socket transport: prefixes, comma-separated, `^` excludes, `=` exact names. Typical use: `^lo,docker` or an explicit fabric/Ethernet NIC |
| `NCCL_IB_HCA` | Which IB/RoCE adapters: comma list of `hca[:port[:rail[:plane]]]`, `^` exclude, `=` exact names (otherwise prefixes). Example `mlx5_0,mlx5_1,...` |
| `NCCL_IB_DISABLE` | Disable the IB transport (falls back to sockets; a performance cliff, used to test) |
| `NCCL_IB_GID_INDEX` | GID index for RoCE (default -1); find it with `show_gids` |
| `NCCL_IB_TIMEOUT` | Verbs timeout, 4.096 µs x 2^value; raise on very large networks if you see `ibv_poll_cq` error 12 |
| `NCCL_CROSS_NIC` | Whether rings may use different NICs on different nodes; depends on whether the fabric is rail-optimised |
| `NCCL_NET_GDR_LEVEL` (formerly `NCCL_IB_GDR_LEVEL`) | Maximum GPU-NIC distance for GPUDirect RDMA |
| `NCCL_P2P_LEVEL`, `NCCL_P2P_DISABLE`, `NCCL_SHM_DISABLE` | Limit or disable intra-node transports (diagnosis) |
| `NCCL_ALGO`, `NCCL_PROTO` | Force algorithm (ring, tree, ...) or protocol; override NCCL's tuning (use only to test) |
| `NCCL_TOPO_DUMP_FILE` / `NCCL_TOPO_FILE` | Dump the detected topology XML / supply one (virtualised or unusual hosts) |
| `NCCL_BUFFSIZE` | Size of internal NCCL communication buffer in bytes; if tuning for large all-reduce operations, start at `4 MB` (`4194304`) and increase stepwise while watching GPU memory pressure |
| `NCCL_NSOCKS_PERTHREAD`, `NCCL_SOCKET_NTHREADS` | Socket/TCP transport threads and sockets per thread; `NCCL_NSOCKS_PERTHREAD` × `NCCL_SOCKET_NTHREADS` cannot exceed `64` sockets total per communicator |
| `NCCL_MIN_NCHANNELS`, `NCCL_MAX_NCHANNELS` | Minimum and maximum number of communication channels (subrings); each channel uses one CUDA block, so leave at default unless tested |
| `NCCL_MNNVL_ENABLE` | Enable multi-node NVLink (`MNNVL`) on systems with multi-node NVLink switches (such as NVL72 GB200/GB300) |
| `NCCL_SHARP_DISABLE` | Set `NCCL_SHARP_DISABLE=1` to disable in-network SHARP aggregation for A/B testing or troubleshooting |
| `NCCL_IGNORE_CPU_AFFINITY` | Set `NCCL_IGNORE_CPU_AFFINITY=1` so NCCL ignores a narrow inherited CPU affinity mask and spreads its proxy/worker threads across cores in the local NUMA domain |
| `NCCL_RAS_ENABLE` etc. | The reliability/availability/serviceability subsystem (newer) |

Practices: set the minimum; default detection is usually right on a well-built node. Put site-wide settings in one file (`NCCL_CONF_FILE` or `/etc/nccl.conf`) or the module, so users do not paste folklore. Re-verify every variable against the NCCL version (the guide has per-variable "since" notes; some are renamed). Record `NCCL_DEBUG=INFO` output from a healthy run as the baseline: it prints the chosen transports (`NET/IB`, `P2P/CUMEM`, `NVLS`), rings, channels, and the HCAs used. An `INFO` line that says `NET/Socket` on an IB cluster is the classic misconfiguration.

PyTorch adds its own: `TORCH_NCCL_ASYNC_ERROR_HANDLING`, `TORCH_NCCL_BLOCKING_WAIT`, process-group timeouts (`init_process_group(timeout=...)`), flight-recorder settings (names vary by version; check). A short timeout turns a silent hang into a crash with a stack, which is what you want in production.

## 6. Binding for training jobs

Targets: each rank on cores of the socket/NUMA node closest to its GPU and NIC; data-loader workers inside the same cpuset; no oversubscription.

- Slurm: `--cpus-per-gpu`, `--cpu-bind=cores` (or `rank`/`map_cpu`), `--gpu-bind=closest`, `--gres-flags=enforce-binding`, and `CoreSpecCount` for the system (6.8, 6.10).
- Threads: `OMP_NUM_THREADS` equals CPUs per rank minus data-loader workers' share; `torch.set_num_threads`; `MKL_NUM_THREADS`.
- Verify: `srun ... bash -c 'echo $SLURM_PROCID $(taskset -pc $$) $CUDA_VISIBLE_DEVICES'`, `nvidia-smi topo -m`, `numactl -s`, and NCCL's INFO output (`GPU Direct RDMA Enabled for GPU x / HCA y` lines show NIC affinity).
- Typical 8-GPU HGX node: two NUMA domains, four GPUs each, NICs distributed (often one per GPU, "rail-optimised"). Rank i should use NIC i; NCCL maps this automatically if topology detection works (containers and VMs can break it: see `NCCL_TOPO_FILE`).
- `--bind-to none` in `mpirun` examples (6.4) is for PyTorch-with-workers cases; under Slurm use `--cpu-bind` instead.

## 7. Framework patterns

- **DDP**: replicate model, all-reduce gradients; launch as above. Set `find_unused_parameters` only if needed (cost).
- **FSDP/ZeRO**: shard parameters, gradients and optimiser state; all-gather and reduce-scatter dominate; sensitive to fabric bandwidth and to rank placement within nodes (shard groups). Use `--ntasks-per-node=8` with consistent ordering (`--distribution=block` default) so that adjacent ranks share a node.
- **DeepSpeed**: its launcher can use `mpirun` or `pdsh`; on Slurm prefer launching with `srun` and `deepspeed` in `--no_ssh`-style or the Slurm runner, configured with a hostfile derived from `scontrol show hostnames`. Verify against the version.
- **Megatron-LM / NeMo**: tensor and pipeline parallel groups are built from the ranks; tensor-parallel groups should fit inside a node (NVLink). Rank-to-node ordering therefore matters; keep Slurm's default block distribution and the framework's expected order consistent (Part 14).
- **Checkpointing and resume**: periodic async checkpoints; resume logic keyed on `SLURM_RESTART_COUNT` or on the existence of the latest checkpoint (the toy script shows the pattern); coordinate with `--signal` and `--requeue` (6.11 section 7).
- **Containers**: pyxis/enroot `--container-image` with `--container-mounts`; NCCL and CUDA come from the image; the host provides the driver and the IB device nodes (6.13).

## 8. Failure and diagnosis

| Symptom | Likely causes | First checks |
|---|---|---|
| Hangs at `init_process_group` | Wrong `MASTER_ADDR`/port, firewall, a rank failed to start, version mismatch, one node's image pull slow | Per-rank logs, `ss -ltnp` on master, `srun -l hostname`, compare environment per node |
| Hangs at first collective | NCCL cannot connect (wrong interface/HCA, `NCCL_SOCKET_IFNAME` picked docker0), IB link down, GID/RoCE misconfiguration | `NCCL_DEBUG=INFO`, `ibstat`, `NCCL_IB_HCA`, `show_gids` |
| Runs but slow | Fell back to sockets, no GDR, wrong NIC mapping, cross-NIC on a rail fabric, CPU bound data loader, oversubscribed threads, throttled GPU | INFO transports, `nccl-tests` all_reduce_perf on the allocation, `nvidia-smi dmon`, `top` |
| One rank dies, others hang until time limit | No `-K`/`--kill-on-bad-exit`, no NCCL async error handling or timeout | `srun -K`, set timeouts, flight recorder |
| Sporadic hangs at scale | A flapping link or sick node; congestion; rank desync | Fabric error counters (Part 12), per-node GPU/XID errors, rerun excluding nodes (`--exclude`) |
| `NCCL WARN ... unhandled system error` | Verbs errors, memlock limits, missing devices in container | `ulimit -l unlimited` (limits in slurm/systemd), device nodes, `dmesg` |
| OOM only at larger scale | Memory per rank, cache allocator fragmentation, NCCL buffers | per-rank memory logs |
| Different speed per rerun | Placement/topology variance, noisy neighbours | `--switches`, exclusive nodes, topology config (6.8) |

Method: reproduce small first (1 node, then 2), run `nccl-tests` (`all_reduce_perf -b 8 -e 8G -f 2 -g 1`, untested here) with `srun` on the same allocation to separate fabric problems from application problems (6.28), compare to baseline bus bandwidth for the node type, and bisect by node subsets.

### 8.1 Six multinode communication pitfalls

From *AI Systems Performance Engineering* (Chapter 4), six host- and launch-level communication pitfalls account for most multinode slowdowns and stalls:

1. **Using a CPU-bound `gloo` backend instead of `nccl`:** If `dist.init_process_group(backend="gloo")` is used (or fallen back to) instead of `backend="nccl"`, collectives run through host CPU memory and TCP sockets instead of GPUDirect RDMA. In the book's 400 MB (`100M` float32 elements) all-reduce example across 8 GPUs on `800 Gb/s` (`100 GB/s`) InfiniBand, `gloo` over a `2 GB/s` TCP path takes `~200 ms` (`200.00 ms`), whereas `nccl` over `100 GB/s` InfiniBand takes `~4 ms` (`4.00 ms`). Verify the active backend with `torch.distributed.get_backend()` (untested here).
2. **Mismatched `NCCL` versions across nodes or libraries:** Running PyTorch's bundled `NCCL` against a different system `libnccl` (`nvidia-nccl-cu*`), or running different versions across nodes, causes hangs or silent fallbacks. Inspect `torch.cuda.nccl.version()` (untested here) on every rank at startup.
3. **TCP port exhaustion during `NCCL` bootstrap:** `NCCL` uses ephemeral TCP ports for its out-of-band setup handshake. If the host range is too narrow, handshakes stall or fail. Widen `/proc/sys/net/ipv4/ip_local_port_range` (or set `net.ipv4.ip_local_port_range="50000 51000"` in `/etc/sysctl.conf`, untested here) alongside explicit `NCCL_SOCKET_IFNAME` and `MASTER_PORT`.
4. **Insufficient network bandwidth or falling back to `eth0` / `docker0` / `lo` instead of `ib0`:** Missing `/dev/infiniband` device mounts in containers, mismatched RoCE GID indices, or unconfigured interfaces cause `NCCL` to silently fall back from InfiniBand/RoCE to slower management Ethernet. Check `NCCL_DEBUG=INFO`, set `NCCL_IB_DISABLE=0` and `NCCL_SOCKET_IFNAME=ib0` (untested here), confirm `lsmod | grep nvidia_peermem` (untested here), and monitor NIC bytes with `nvidia-smi dmon`, `ethtool -S <iface>`, or `ip -s link show <iface>` (untested here).
5. **Straggler nodes or processes:** In synchronous collectives, the slowest node or GPU sets the step time for every rank. Enable `TORCH_NCCL_ENABLE_MONITORING=1` and `TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC` (alongside `torch.distributed.monitored_barrier` and `TORCH_NCCL_ASYNC_ERROR_HANDLING=1`, untested here) to detect and abort stalled ranks instead of hanging the allocation.
6. **GPU memory fragmentation under UCX/RDMA:** PyTorch's caching allocator holds freed blocks in its cache without returning them to the OS or UCX registration pool. In the book's 10-iteration example, pre-allocating a `0.800 GB` buffer (`torch.empty(int(2e8))`) and repeatedly allocating and freeing `~40 MB` and `~200 MB` tensors leaves `torch.cuda.memory_allocated()` at `0.000 GB` after freeing, while `torch.cuda.memory_reserved()` grows from `0.800 GB` at iter 0 to `1.040 GB` at iter 1 and `1.240 GB` from iter 2 through iter 10. Mitigate fragmentation with `PYTORCH_ALLOC_CONF="max_split_size_mb:128,expandable_segments:True"` (untested here).

### 8.2 Six `NCCL` communicator lifecycle and environment gotchas

1. **Creating `NCCL` communicators too often (inside the training loop):** `dist.init_process_group("nccl")` (or `ncclCommInitRank` in C++) performs all-to-all handshakes, exchanges unique IDs, builds rings/trees, and allocates GPU buffers. Creating 32 separate communicators across 32 GPUs can take `2–3 minutes` instead of `2–3 seconds`. In the book's Table 4-3 example, calling `init_process_group` and `destroy_process_group` inside the iteration loop costs `48.0 ms` per iteration versus `0.5 ms` for the 1-element `dist.all_reduce` itself (`48.5 ms` total per iteration before fix versus `0.5 ms` after moving initialization outside the loop, saving `>98%` per-step time).
2. **Recreating subcommunicators on every step:** For tensor or pipeline parallelism subgroups, create subcommunicators once at startup with `torch.distributed.new_group()` (or batch C++ initializations inside `ncclGroupStart()`, `ncclCommInitRank(...)`, and `ncclGroupEnd()`, untested here) and reuse them across iterations; all participating ranks must call creation and destruction in lockstep.
3. **Overtuning or leaving diagnostic environment variables enabled:** Never leave `NCCL_P2P_DISABLE=1` or `NCCL_SHM_DISABLE=1` set in production after debugging, because they force intranode GPU traffic through host-staged memory or network paths, raising latency from a few microseconds to tens of microseconds and cutting bandwidth from hundreds of GB/s to tens of GB/s; similarly, lower `NCCL_DEBUG` from `INFO`/`DEBUG` to `WARN` or `VERSION` after troubleshooting. When tuning socket transport, `NCCL_NSOCKS_PERTHREAD` × `NCCL_SOCKET_NTHREADS` cannot exceed `64` sockets total; when tuning `NCCL_BUFFSIZE`, start at `4 MB` (`4194304`) and monitor VRAM; leave `NCCL_MIN_NCHANNELS` / `NCCL_MAX_NCHANNELS` at defaults unless needed; use `NCCL_TOPO_FILE` (captured via `NCCL_TOPO_DUMP_FILE`), `NCCL_MNNVL_ENABLE`, and `NCCL_SHARP_DISABLE` deliberately.
4. **Collapsed CPU-GPU NUMA affinity for `NCCL` proxy threads:** When a launcher pins a rank to a very narrow CPU mask, `NCCL`'s background network-polling and kernel-dispatch threads can collapse onto a single core. Bind each rank to its GPU's local NUMA domain (for example GPUs 0–3 on NUMA node 0 and GPUs 4–7 on NUMA node 1) and set `NCCL_IGNORE_CPU_AFFINITY=1` (untested here) so `NCCL` ignores the narrow inherited CPU mask and spreads its worker threads across cores in the local NUMA node.
5. **Ignoring `NCCL` warnings in logs:** Warnings such as `"unable to enable P2P, falling back to copy"` (GPUs across unsupported PCIe root complexes staging through host RAM) or `NCCL INFO NET/Socket: using Ethernet interface eth0` instead of `ib0` explain major throughput losses and must be fixed via GPU placement or `NCCL_SOCKET_IFNAME=ib0`.
6. **Unhandled `NCCL` communicator hangs and hardware failure rates at scale:** When one rank crashes or hits a hardware fault, collectives on surviving ranks hang unless asynchronous abort is enabled (`TORCH_NCCL_ASYNC_ERROR_HANDLING=1` / `NCCL_ASYNC_ERROR_HANDLING=1`). At scale, hardware interruptions are routine: in Meta's Llama 3 405B 54-day pretraining run on `16,384` H100 GPUs, the job experienced `419` unexpected interruptions (`~7.8`/day) while maintaining `>90%` effective training time. In the book's Table 4-4 breakdown of those interruptions, faulty GPUs caused `148` (`30.1%`), GPU HBM3 memory caused `72` (`17.2%`), software bugs caused `54` (`12.9%`), network switch/cable issues caused `35` (`8.4%`), unplanned host maintenance caused `32` (`7.6%`), GPU SRAM memory caused `19` (`4.5%`), GPU system processor caused `17` (`4.1%`), NIC caused `7` (`1.7%`), and `NCCL` watchdog timeouts caused `7` (`1.7%`).

## 9. Lab

Tested part (laptop): 1) Create a venv with PyTorch (CPU). 2) Run `python fake_srun.py 2 2 python ddp_toy.py` twice and confirm `start_step` goes from 0 to 1. 3) Change the world to 2 nodes x 4 tasks; confirm the all-reduce assertion. 4) Break it: unset `MASTER_ADDR` in `fake_srun.py` and observe that the node name does not resolve.

Untested part (cluster): 5) Run the `srun` style and the `torchrun` style on 2 nodes with `NCCL_DEBUG=INFO`; save logs; find the transport lines. 6) Run `all_reduce_perf` across 2 nodes and record bus bandwidth. 7) Deliberately set `NCCL_IB_DISABLE=1` and compare. 8) Kill one rank mid-run with and without `-K`. 9) Print `taskset -pc` and GPU per rank with and without `--gpu-bind=closest`. 10) Write the site's standard multi-node template.

## 10. Interview angles

- Walk through what happens from `sbatch` to the first all-reduce on 32 nodes.
- `srun` per GPU versus `torchrun` per node: trade-offs?
- Where do `RANK` and `WORLD_SIZE` come from under Slurm? How is `MASTER_ADDR` chosen?
- A 128-GPU job hangs at start; 16 GPUs fine. What do you check?
- Which NCCL variables do you set and why? Which do you avoid?
- How would you prove the job is using InfiniBand and GPUDirect RDMA?
- Why do tensor-parallel groups stay inside a node?
- What happens when one rank crashes? How do you make the job fail fast?

## 11. Checkpoint questions (25)

1. What does Slurm do versus the framework versus NCCL?
2. Does PyTorch use PMIx?
3. What variables does `env://` need?
4. How do you obtain `MASTER_ADDR` from Slurm?
5. Why derive `MASTER_PORT` from the job id?
6. Compare srun-per-GPU and torchrun-per-node.
7. What does `--kill-on-bad-exit` do?
8. What does `SLURM_LOCALID` map to?
9. Why does the harness set `MASTER_ADDR=127.0.0.1`?
10. What did `weights_identical=True` prove?
11. What is the OpenMP runtime clash and its fix?
12. What does `NCCL_DEBUG=INFO` show?
13. How are `NCCL_SOCKET_IFNAME` prefixes and `^` interpreted?
14. What format does `NCCL_IB_HCA` take?
15. What is `NCCL_IB_GID_INDEX` for?
16. How is `NCCL_IB_TIMEOUT` computed?
17. When use `NCCL_ALGO`?
18. What is `NCCL_CROSS_NIC` about?
19. How do you verify CPU/GPU binding?
20. Why does rank placement matter for FSDP and tensor parallelism?
21. Why set a process-group timeout and initialize `dist.init_process_group("nccl")` once outside the training loop, and what did Meta's 54-day Llama 3 405B run on `16,384` H100 GPUs show about failures at scale? **A:** A short timeout plus `TORCH_NCCL_ASYNC_ERROR_HANDLING=1`, `TORCH_NCCL_ENABLE_MONITORING=1`, and `TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC` turns silent rank hangs into fast aborts (`419` unexpected interruptions, `~7.8`/day, occurred in Meta's 54-day run: `148` GPU/NVLink = `30.1%`, `72` HBM3 = `17.2%`, `54` software bugs = `12.9%`, `35` network switch/cable = `8.4%`); initializing `nccl` once outside the loop avoids the `48.0 ms` per-iteration setup/teardown cost vs `0.5 ms` for the `all_reduce` (`48.5 ms` → `0.5 ms`, saving `>98%`).
22. How do you separate fabric problems from application problems?
23. What does a `NET/Socket` line on an IB cluster mean?
24. Why exclusive nodes for benchmarks?
25. What resume logic should a training script have?

## 12. Sources and review notes

- Launch layering, PMIx and torchrun/srun patterns, NCCL tuning discussion: the author's NVIDIA-DevOps volume-10 chapter 7 (sections 3 to 6), and *Distributed AI Systems* chapter 8 (DDP, FSDP, DeepSpeed, Megatron-LM with Slurm; environment variables; failure handling), restated in my words with version caveats added.
- `ai-systems-performance-engineering` — Chris Fregly, *AI Systems Performance Engineering*, "Chapter 4. Tuning Distributed Networking Communication" (read in full): the 6 multinode communication pitfalls (`gloo` `~200 ms` at `2 GB/s` TCP vs `nccl` `~4 ms` at `100 GB/s` / 800 Gbps IB for a 400 MB all-reduce; mismatched `NCCL` versions via `torch.cuda.nccl.version()`; TCP port exhaustion `net.ipv4.ip_local_port_range="50000 51000"`, `NCCL_SOCKET_IFNAME`, `MASTER_PORT`; fallback to `eth0`/`docker0`/`lo` vs `ib0` with `NCCL_DEBUG=INFO` and `NCCL_IB_DISABLE=0`; straggler monitoring with `TORCH_NCCL_ENABLE_MONITORING=1` and `TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC`; GPU memory fragmentation under UCX/RDMA where `0.800 GB` allocated reserves `1.240 GB` without `PYTORCH_ALLOC_CONF="max_split_size_mb:128,expandable_segments:True"`) and the 6 `NCCL` communicator lifecycle and environment gotchas (Table 4-3 `init_process_group` `48.0 ms` + `0.5 ms` `all_reduce` = `48.5 ms` vs `0.5 ms` initialized once saving `>98%`; `NCCL_NSOCKS_PERTHREAD` × `NCCL_SOCKET_NTHREADS` ≤ `64`, `NCCL_BUFFSIZE` starting at `4 MB` / `4194304`, `NCCL_MIN_NCHANNELS`/`NCCL_MAX_NCHANNELS`, `NCCL_TOPO_FILE`, `NCCL_MNNVL_ENABLE`, `NCCL_SHARP_DISABLE`; `NCCL_IGNORE_CPU_AFFINITY=1`; Table 4-4 Llama 3 405B 54-day run on `16,384` H100 GPUs with `419` unexpected interruptions, `~7.8`/day, `>90%` effective training time). Deep NCCL internals, SHARP/NVLS, and NIXL are covered in Part 12 and Part 15.
- NCCL variable semantics: NVIDIA/nccl `docs/userguide/source/env.rst` (commit `3e46c08`).
- Slurm options: man pages as in 6.10 and 6.11.
- Original and run: `slurm_dist_init.py`, `ddp_toy.py`, `fake_srun.py` (PyTorch 2.14.1, gloo, macOS) with the output above.
- Unverified: multi-node NCCL behaviour, DeepSpeed/Megatron launch flags for current versions, PyTorch NCCL environment variable names, topology layout of HGX nodes.
