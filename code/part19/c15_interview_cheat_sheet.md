## A. Linux triage

| Fact | Source |
|---|---|
| First 60 seconds, in order: `uptime`, `dmesg -T \| tail`, `vmstat -SM 1`, `mpstat -P ALL 1`, `pidstat 1`, `iostat -sxz 1`, `free -m`, `sar -n DEV 1`, `top` | 20.3 | <!--a: dmesg -T | tail || vmstat -SM 1 || iostat -sxz 1-->
| Start from the problem statement: what, since when, what changed, who. Then USE for the host and RED for the service | 20.3 | <!--a: what changed-->
| Load on Linux counts tasks in uninterruptible sleep, so high load with an idle CPU can mean slow disk | 20.5 | <!--a: uninterruptible-->
| Disk `%util` at 100 does not prove saturation. Read `await` and the queue size next to it | 20.3 | <!--a: await-->
| Bytes free but writes fail: `df -i` shows the inode count, a separate resource that also gives ENOSPC | 20.4 | <!--a: df -i-->
| Open files: compare `/proc/PID/fd` with `/proc/PID/limits`. Deleted but still open: `lsof +L1` | 20.4 | <!--a: lsof +L1-->
| CPU throttling shows in `cpu.stat` as `nr_throttled` and `throttled_usec`. Sample twice and compare | 20.5 | <!--a: nr_throttled-->
| An OOM log line with `CONSTRAINT_MEMCG` means a cgroup limit was hit, not the whole node | 20.5 | <!--a: constraint_memcg-->
| Exit 143 is death by TERM. Exit 137 is KILL, often the OOM killer. The rule is 128 plus the signal number | 20.7 | <!--a: 143 || 137-->
| GPU job slow while the pod is Running: check CPU throttling on the data-loader processes before blaming the GPU | 5.9 | <!--a: throttl-->

## B. Networking

| Fact | Source |
|---|---|
| Connection refused is an immediate answer, usually nothing listening. A timeout means a packet or its reply was dropped | 20.6 | <!--a: refused-->
| Two queues can overflow: the SYN backlog and the accept queue. Many `CLOSE-WAIT` sockets mean our application did not close them | 20.6 | <!--a: close-wait || somaxconn-->
| Large responses hang while small ones work: suspect an MTU black hole. An overlay that uses 50 bytes leaves 1,450 | 20.6 | <!--a: 1,450-->
| New connections fail while old ones work: compare the conntrack count with `nf_conntrack_max` | 20.6 | <!--a: nf_conntrack_max-->
| DNS in a pod: `ndots:5` multiplies lookups for a name such as `api.example.com` | 20.6 | <!--a: ndots-->
| Do not test a training fabric with `iperf3`. It uses the kernel TCP stack and training does not | 19.5 | <!--a: iperf3-->
| A 4x NDR InfiniBand link carries 400 Gbps, which is 50 GB/s. Divide bits by eight | 19.5 | <!--a: 400 gbps || 50 gb/s-->
| PCIe Gen5 x16 gives roughly 64 GB/s per direction | 19.5 | <!--a: 64 gb/s-->
| Host-side RDMA tools: `ib_write_bw` and `ib_write_lat` test the wire. `ib_write_bw --use_cuda` tests the GPU memory path | 19.5 | <!--a: ib_write_bw || use_cuda-->
| Pause frames rising by millions per second in `ethtool -S` point to a PFC storm from badly tuned ECN | 12.4 | <!--a: pfc-->

## C. Kubernetes debug order

| Symptom | Owner and first object to read | Source |
|---|---|---|
| Pending, no node | scheduler: Pod events, node Allocatable and taints | 20.23 | <!--a: allocatable-->
| ImagePullBackOff | kubelet and runtime: Pod events, registry | 20.23 | <!--a: imagepullbackoff-->
| Restarts rising | kubelet: `Last State`, probe events, `logs --previous` | 20.23 | <!--a: logs --previous-->
| Missing from a Service | EndpointSlice controller: Pod Ready condition, selector | 20.23 | <!--a: endpointslice-->
| Replicas not following load | HPA: conditions and metrics | 20.23 | <!--a: hpa-->
| Pods vanish when a node dies | node controller: Node conditions, taints | 20.23 | <!--a: taints-->

| Fact | Source |
|---|---|
| Restart back-off starts at 10 s, doubles, and caps at 300 s | 20.23 | <!--a: 300-->
| Kubelet sends SIGTERM, waits the grace period (30 s by default), then KILL | 20.7 | <!--a: sigterm-->
| GPUs are an integer extended resource, `nvidia.com/gpu`, requested in `limits` | 11.2 | <!--a: nvidia.com/gpu-->
| One pod can never span nodes. A multi-node job is a gang of pods that must start together | 11.7 | <!--a: gang-->
| Topology Manager with `single-numa-node` keeps the GPU, CPU cores and memory on one NUMA node | 11.6 | <!--a: single-numa-node-->
| A PodDisruptionBudget with zero allowed disruptions blocks a node drain | 20.23 | <!--a: poddisruptionbudget || pdb-->

## D. GPU facts

| Fact | Source |
|---|---|
| H100 SXM: 80 GB memory, 3.35 TB/s bandwidth (NVIDIA H100 page) | 20.12 | <!--a: 3.35 tb/s-->
| H100 BF16 dense Tensor Core peak: 989 TFLOPS. The 1,979 on the datasheet assumes sparsity | 9.2 | <!--a: 989 tflops-->
| DGX H100 has 8 x 80 GB, 640 GB total. DGX H200 has 8 x 141 GB, 1,128 GB total | 9.1 | <!--a: 640 gb || 1,128 gb-->
| NVLink per GPU: 900 GB/s on Hopper, 1.8 TB/s on Blackwell | 9.1 | <!--a: 900 gb/s || 1.8 tb/s-->
| Blackwell HBM3e is about 8 TB/s per GPU, 2.4 times Hopper at 3.35 TB/s | 10.7 | <!--a: 8 tb/s-->
| An NVL72 GPU has 18 NVLink 5 ports at 100 GB/s each, 1.8 TB/s in all | 9.5 | <!--a: 18 nvlink-->
| H100 80GB MIG profiles: 1g.10gb x7, 1g.20gb x4, 2g.20gb x3, 3g.40gb x2, 4g.40gb x1, 7g.80gb x1 | 19.8 | <!--a: 1g.10gb || 7g.80gb-->
| A100 40GB MIG profiles: 1g.5gb x7, 2g.10gb x3, 3g.20gb x2, 7g.40gb x1 | 19.8 | <!--a: 1g.5gb-->
| MIG gives hardware isolation. Time-slicing shares memory and cache with no hardware boundary | 11.25 | <!--a: time-slicing-->
| In `nvidia-smi topo -m` on a healthy DGX H100, GPU pairs show `NV18`. A GPU and NIC pair to benchmark shows `PIX`. `SYS` crosses the CPU socket link | 19.5, 9.2 | <!--a: nv18 || pix || sys-->

## E. NCCL and fabric

| Fact | Source |
|---|---|
| busbw = algbw x factor. AllReduce factor is 2(n-1)/n, AllGather and ReduceScatter (n-1)/n | 19.5 | <!--a: 2(n-1)/n-->
| Compare busbw, not algbw, with the link rate. busbw stays flat as ranks grow on a healthy fabric | 19.5 | <!--a: stays flat-->
| 16 ranks, 1 GiB AllReduce in 44,739.2 us: algbw 24.00 GB/s, busbw 45.00 GB/s, 90 percent of a 50 GB/s link | 19.5 | <!--a: 44739.2-->
| Never report bandwidth from a run whose `#wrong` is not zero. `-c` defaults to 1 | 19.5 | <!--a: #wrong-->
| Under 1 GB/s with `Using network Socket` in the log is the silent fallback, for example `NCCL_IB_DISABLE=1` | 19.5 | <!--a: using network socket || nccl_ib_disable-->
| Bootstrap hang: set `NCCL_SOCKET_IFNAME=^docker,lo` | 19.5 | <!--a: nccl_socket_ifname-->
| NCCL 2.31 `NCCL_RUN_DIAGNOSTICS=1` runs checks at init. RAS exists since 2.24, port 28028 | 19.5 | <!--a: nccl_run_diagnostics || 28028-->
| In a hung collective the ranks that print timeouts are the healthy ones. Find the rank that never arrived | 19.5 | <!--a: never arrived-->
| Bisect a slow cluster: ceil(log2 N) rounds, 3 for 8 nodes, 7 for 128 | 19.5 | <!--a: log2 n-->
| Default DDP gradient bucket is 25 MB. Many small buckets make training slow while the wire test passes | 19.5 | <!--a: 25 mb-->
| 54-day Llama 3 405B run: faulty GPU 30.1 percent of interruptions as printed in the paper (its own counts give 148 of 419, which is 35.3 percent), HBM3 17.2, software 12.9, switch or cable 8.4, NIC 1.7 | 19.5 | <!--a: 30.1 percent-->

## F. Training numbers

| Fact | Source |
|---|---|
| Training compute is about 6 x parameters x tokens FLOPs | 9.10 | <!--a: 6 multiplied by parameter count-->
| 70B model, 100B tokens: 4.2e22 FLOPs, 9.6 days on 128 H100 at 40 percent MFU | 9.10 | <!--a: 9.6 days-->
| MFU = achieved model FLOPS divided by peak. 430 of 989 TFLOPS is 43.48 percent | 9.2 | <!--a: 43.48-->
| Llama 3 scale: about 50,700 GPU-hours per interruption, so the job MTBF falls as GPU count rises | 19.4 | <!--a: 50,700-->
| Checkpoint interval from Young: tau = sqrt(2 x C x M), with C the blocking write time and M the job MTBF | 19.4 | <!--a: sqrt(2-->
| Job MTBF is node MTBF divided by node count when nodes fail independently. Measure it from logs | 19.4 | <!--a: memoryless and independent-->
| Two-stage checkpoint: copy shards to host DRAM or local NVMe in seconds, then flush to shared storage in the background | 13.7 | <!--a: pinned host dram-->
| 16,384 GPUs, job MTBF 3.09 h, 22.5 s blocking write, 600 s restart: Daly interval 685 s, waste 11.47 percent. Async 2 s write: 209 s, 7.22 percent | 19.4 | <!--a: 685 s || 11.47 percent || 7.22 percent-->
| FSDP shards parameters, gradients and optimiser state across all GPUs instead of replicating them on every rank | 14.5 | <!--a: shards them across all gpus-->

## G. Inference numbers

| Fact | Source |
|---|---|
| KV bytes per token = 2 x layers x KV heads x head dim x bytes per element | 20.12 | <!--a: 2 x layers-->
| Qwen3-8B BF16: 147,456 B per token. A 2,500-token request needs 0.36864 GB | 20.12 | <!--a: 147,456-->
| Llama 3.1 8B BF16: 32 layers, 8 KV heads, head dim 128, so 131,072 B per token | 19.3 | <!--a: 131,072-->
| Weights in GB at half precision = billions of parameters x 2. An 8B model is about 16.4 GB | 20.12 | <!--a: 16.4 gb-->
| Batch-one decode ceiling = memory bandwidth divided by weight bytes. 3.35 TB/s and 16.4 GB give about 204 tokens/s | 20.12 | <!--a: 204-->
| Prefill is compute-bound and decode is memory-bandwidth-bound, so they can be split onto separate pools | 15.1 | <!--a: compute-bound prefill || memory-bandwidth-bound decode-->
| End-to-end latency = TTFT + ITL x (N - 1). 0.4 + 0.04 x 499 = 20.36 s | 20.19 | <!--a: 20.36-->
| A hang can still return 200 on `/health` in vLLM v0.32.0, so alert on token rate | 20.18 | <!--a: /health-->
| 429 means this tenant is over its limit. 503 means this server is overloaded or draining | 20.21 | <!--a: 429-->

## H. Storage and bandwidth arithmetic

| Fact | Source |
|---|---|
| A 112 GB checkpoint on a shared file system absorbing 5 GB/s blocks the job for about 22.5 s. Time is size over bandwidth | 19.4 | <!--a: 22.5 seconds || 112 gb-->
| Mixed-precision checkpoint with Adam state costs 14 bytes per parameter. 8.03 billion parameters is about 112 GB | 19.4 | <!--a: 14 bytes per parameter-->
| Millions of tiny files make the storage system spend its time opening them, so GPUs wait for data | 13.6 | <!--a: millions of tiny files-->
| GPUDirect Storage removes the host bounce buffer between storage and GPU memory | 13.3 | <!--a: host bounce buffer-->

## I. Observability and SLOs

| Fact | Source |
|---|---|
| Burn rate = error ratio / (1 - SLO). Hours to empty = period hours / burn rate | 20.19 | <!--a: burn_rate-->
| 99.9 percent over 30 days is 43.2 minutes of full outage. A 1 percent error ratio is burn 10, empty in 72 hours | 20.19 | <!--a: 72 hours-->
| Workbook alerts for 99.9 percent: page at 14.4 (1 h and 5 min), page at 6 (6 h and 30 min), ticket at 1 (3 d and 6 h) | 20.19 | <!--a: 14.4-->
| Page on gateway SLO burn. Engine metrics explain a burn and do not page | 20.19 | <!--a: gateway-->
| `rate` before `sum`. Keep `le` in `histogram_quantile`. Never average p99 values | 20.25 | <!--a: histogram_quantile-->
| Alertmanager defaults: `group_wait` 30 s, `group_interval` 5 min, `repeat_interval` 4 h | 20.25 | <!--a: group_wait-->
| Alert on DCGM exporter counters for Xid and ECC, and keep label cardinality inside a budget | 19.7 | <!--a: cardinality-->

## J. Failure signatures and Xid actions

| Signal | What the catalog or chapter says to do | Source |
|---|---|---|
| Xid 13, 31, 32 | Restart the application | 19.6 | <!--a: restart_app-->
| Xid 43, 63, 92 | Ignore the immediate action. Track the rate | 19.6 | <!--a: ignore-->
| Xid 45 | Depends: alone, restart the fabric manager. Otherwise follow the earlier Xid | 19.6 | <!--a: workflow_xid_45-->
| Xid 48 (double-bit ECC) | Reset the GPU. Together with Xid 63 or 64, drain and reset | 19.6 | <!--a: drain and reset-->
| Xid 64, 95, 119, 120 | Reset the GPU | 19.6 | <!--a: reset_gpu-->
| Xid 74 (NVLink error) | NVLink workflow, then contact support. Reset or reboot clears it | 19.6 | <!--a: workflow_nvlink_err-->
| Xid 79 (fell off the bus) | The catalog action is restart of the bare-metal node. 20.16 and 20.18 word it differently, so read the live catalog | 19.6, 20.16 | <!--a: restart_bm-->
| TTFT p99 high | Queue growth, cache hit collapse, KV exhaustion. Check queue time against waiting requests | 20.18 | <!--a: vllm:request_queue_time_seconds-->
| Tokens per second zero | Hang, Xid fault or crash loop. Read `dmesg` and the NCCL log | 20.18 | <!--a: dmesg-->
| Pods restarting | Liveness kill, startup OOM or runtime OOM. Read Last State | 20.18 | <!--a: last state-->

## K. Design speaking plan, 45 minutes

| Minutes | What to say | Source |
|---|---|---|
| 0 to 5 | Requirements, assumptions and a back-of-envelope estimate. Start with numbers, not boxes | 20.13 | <!--a: requirements and numbers, not boxes-->
| 5 to 10 | API contract, control plane and data plane | 20.13 | <!--a: control-->
| 10 to 26 | Gateway and limits, then router and cache | 20.13 | <!--a: router-->
| 26 to 36 | Pools, placement, autoscaling and regions | 20.13 | <!--a: autoscaling-->
| 36 to 45 | Isolation, failure modes, observability and rollout | 20.13 | <!--a: rollout-->
| Estimate method | Demand, per-GPU ceiling, times 0.9, round up, add a spare | 20.12 | <!--a: 0.9-->

## L. Behavioural and closing

| Fact | Source |
|---|---|
| Project deep dive, "what would you change": name one change, the evidence, what you would measure first, and what you would leave alone | 20.28 | <!--a: what you would leave alone-->
| When you do not know: say what you know, name the nearest mechanism, say how you would check. Never present a guessed flag as certain | 20.29 | <!--a: never guess a flag-->
| Questions to ask: on-call load, how reliability is measured, the biggest recent incident class | 20.28 | <!--a: how is the rota built-->
| Incident script: confirm impact, declare severity, ask what changed, pick a reversible mitigation first | 20.26 | <!--a: what changed-->
