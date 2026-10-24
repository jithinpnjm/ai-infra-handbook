---
id: "c03-10"
title: "3.10 Python for data and ML infrastructure: NumPy, pandas, PyTorch essentials"
sidebar_label: "3.10 Python for data and ML infrastructure: NumPy, pandas, PyTorch essentials"
sidebar_position: 10
description: "What an infrastructure engineer needs from NumPy, pandas, Arrow and PyTorch: memory layout, vectorisation, dataframes at scale, tensors, autograd, devices, data loading, mixed precision, profiling and the failure modes of ML code"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.10 Python for data and ML infrastructure: NumPy, pandas, PyTorch essentials

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | Python 3.11+, `pip install numpy pandas pyarrow torch`; GPU optional |
| Part | Part 3: Python for infrastructure |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

You will not be hired to design neural networks, but you will be paged when a training job is slow, a data loader starves the GPUs, an out-of-memory error kills a run at hour 40, or a notebook leaks 200 GB of RAM. Diagnosing those needs working fluency in the stack that ML engineers use: **NumPy** (the array model underneath everything), **pandas and Arrow** (tabular data), and **PyTorch** (tensors, autograd, modules, devices, data loading, mixed precision, distributed hooks). This chapter is deliberately infrastructure-oriented: memory layout and copies, where time goes, what runs on the CPU versus the GPU, and how to measure. It is not a machine-learning course; model theory is in Part 14.

## Prerequisites and outcomes

Needs 3.1 to 3.6 (Python core, generators, concurrency). After this chapter you can:

- Explain the NumPy array model (dtype, shape, strides, views versus copies, broadcasting) and write vectorised code instead of Python loops.
- Use pandas efficiently (dtypes, categorical data, chunking, groupby, joins), know when it breaks (memory, single thread) and when to move to Arrow, Parquet, Polars, DuckDB or Dask/Spark.
- Read and write a PyTorch training loop; explain tensors, devices, autograd, `nn.Module`, optimisers, `DataLoader`, checkpointing, AMP and gradient accumulation.
- Reason about GPU memory (weights, gradients, optimiser state, activations, fragmentation), asynchronous execution, host-device transfers, and profile with the PyTorch profiler.
- Recognise common infrastructure failure modes: dataloader starvation, CPU thread oversubscription, accidental synchronisation, memory leaks from retained graphs, non-determinism, OOM.

## 1. NumPy: the array model

A NumPy `ndarray` is a block of contiguous (usually) typed memory plus metadata: `dtype` (element type), `shape`, and `strides` (bytes to step along each axis). Almost everything else in the Python data ecosystem (pandas, scikit-learn, PyTorch interop, image libraries) is built around this idea or copies it.

```python
import numpy as np
a = np.arange(12, dtype=np.float32).reshape(3, 4)
a.shape, a.dtype, a.strides, a.flags['C_CONTIGUOUS']     # ((3, 4), float32, (16, 4), True)
b = a.T                                                    # a view: same memory, strides swapped, no copy
b.flags['C_CONTIGUOUS']                                    # False
c = np.ascontiguousarray(b)                                # now a copy in new layout
a[0, 0] = 99; b[0, 0]                                      # 99.0: views share memory
np.shares_memory(a, b)                                     # True
```

Concepts to master:

- **dtype determines bytes**: `float64` is 8 bytes, `float32` 4, `float16`/`bfloat16` 2 (NumPy lacks native bfloat16), `int8` 1. A 1 billion element `float64` array is 8 GB; half of that in `float32`. Default floats are `float64`, defaults in deep learning are `float32` or lower, a frequent source of silent 2x memory use and slow GPU transfers.
- **Views versus copies**: basic slicing, reshape (when possible), transpose and `.view()` return views; fancy (integer/boolean array) indexing, `.copy()` and most arithmetic return new arrays. Mutating a view mutates the base: a classic bug. `np.shares_memory` / `.base` check.
- **Memory order**: C order (row-major) vs Fortran order (column-major) changes which loops are cache-friendly; iterating along the contiguous axis is far faster. Non-contiguous arrays often force a copy when passed to C libraries or to `torch.from_numpy`.
- **Broadcasting**: shapes align from the right; axes of size 1 are stretched virtually without copying. `(N,1) + (1,M) -> (N,M)`. It is powerful and the source of silent shape bugs (adding a `(N,)` vector to an `(N,N)` matrix broadcasts along the wrong axis). Assert shapes at function boundaries.
- **Vectorisation**: express computation as whole-array operations (ufuncs, `np.where`, `einsum`, `matmul`) so loops run in C (and BLAS/SIMD), typically 10 to 1000 times faster than Python loops. Avoid Python-level loops over elements; avoid building arrays by repeated `append`/`concatenate` (quadratic); preallocate.
- **Temporary arrays**: `a*b + c` creates intermediates; use in-place ops (`np.add(a, b, out=a)`), `numexpr`, or fuse with `numba`/`jax`/`torch.compile` when memory bandwidth is the bottleneck.
- **Memory mapping**: `np.memmap`/`np.load(mmap_mode="r")` lets multiple processes share a large read-only array via the OS page cache without loading it all (very useful for datasets and token arrays; see Part 13 for storage behaviour).
- **Threads**: NumPy's linear algebra uses a BLAS library (OpenBLAS, MKL) with its own thread pool controlled by `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`. In multi-process data loaders this multiplies (workers x BLAS threads) and oversubscribes cores: set threads to 1 per worker. `threadpoolctl` inspects and limits pools.
- **Numerical issues**: floating-point is not associative (reductions in different orders give different bits), overflow/underflow in `float16`, catastrophic cancellation, NaN propagation (`np.isnan(x).any()`), `np.errstate` to control warnings. Summation across devices differs from single-device results, which matters when comparing runs (determinism, section 8).

```python
# Typical vectorisation: pairwise distances without loops
X = np.random.rand(1000, 64).astype(np.float32)
d2 = (X**2).sum(1)[:, None] - 2 * X @ X.T + (X**2).sum(1)[None, :]
```

## 2. pandas and the tabular stack

**pandas** provides `DataFrame` (labelled 2-D columns, each a NumPy array or extension array) and `Series`. It is the default for exploration and feature engineering on data that fits in memory. For an infrastructure engineer the questions are: how much memory does it use, is it single-threaded, and what replaces it at scale?

```python
import pandas as pd
df = pd.read_csv("events.csv", dtype={"host": "category", "gpu": "int8"}, parse_dates=["ts"], usecols=["ts","host","gpu","util"])
df.memory_usage(deep=True).sum() / 1e6      # MB
df.groupby("host", observed=True)["util"].agg(["mean", "max", "count"])
df.set_index("ts").resample("5min")["util"].mean()
```

Practical rules:

- **Memory**: a DataFrame typically needs 2 to 5 times the file size in RAM during load and transforms. Reduce with narrow dtypes (`int8/16/32`, `float32`), `category` for low-cardinality strings, `usecols`, reading in `chunksize` pieces, and avoid object dtype (Python strings are heavy). Pandas 2 supports Arrow-backed dtypes (`dtype_backend="pyarrow"`, `string[pyarrow]`) that cut string memory and speed up I/O.
- **Avoid row-wise Python**: no `for i, row in df.iterrows()` and minimise `apply(axis=1)`; use vectorised column ops, `np.where`, `merge`, `groupby`. Chained indexing (`df[a][b] = x`) may modify a copy: use `.loc[mask, "col"] = x`; copy-on-write semantics in recent pandas versions reduce this hazard.
- **Joins and groupbys** can explode memory (many-to-many merges). Check key uniqueness (`validate="one_to_one"`), sort/index to speed joins, drop unneeded columns first.
- **Time series**: timezone-aware timestamps (UTC), `resample`, `rolling`, `shift`; be careful with look-ahead leakage when building features (using future data to compute a feature for the past makes models look great offline and fail in production).
- **Single-threaded by default**: for heavy transforms use Polars (multi-threaded, lazy, Arrow-native), DuckDB (in-process analytical SQL over Parquet/CSV), Dask (partitioned pandas across cores or a cluster), Ray Data, Spark. Choose by data size and team skills: fits RAM then pandas/Polars; larger than RAM but one machine then DuckDB/Polars streaming; many TB then Spark/Ray/Dask on a cluster.

### Columnar formats: Parquet and Arrow

- **Parquet** is a compressed, columnar on-disk format with row groups, per-column statistics and predicate pushdown: reading three columns of fifty reads only those bytes. Prefer Parquet (with zstd or snappy) over CSV/JSON for any dataset beyond toy size; choose row-group sizes (roughly 128 MB to 1 GB per file; many tiny files hurt object stores and metadata services), and partition directories by low-cardinality keys (date) with care.
- **Apache Arrow** is the in-memory columnar format that lets pandas, Polars, Spark, DuckDB, Ray and GPU dataframes (RAPIDS cuDF) exchange data without serialisation (zero-copy). `pyarrow.parquet.read_table(..., columns=[...], filters=[...])`, memory-mapped IPC files, and `pyarrow.dataset` for lazily scanning directories.
- **Webdataset / TFRecord / MDS (MosaicML Streaming)**: sharded sequential record formats for very large training sets (images, tokens) that turn many small random reads into large sequential reads, essential on network file systems and object stores (Part 13).
- **GPU dataframes**: RAPIDS **cuDF** offers a pandas-like API on GPU (`cudf.pandas` accelerator mode can run unmodified pandas code on GPU where supported); beneficial for large joins/groupbys when the data already lives near the GPU. Verify support and speedups per workload.

## 3. PyTorch fundamentals

### 3.1 Tensors and devices

A `torch.Tensor` is NumPy's array model plus a **device** (cpu, cuda:0, mps) and **autograd** metadata. Same ideas: dtype, shape, strides, views versus copies, broadcasting.

```python
import torch
x = torch.randn(4096, 4096)                 # CPU, float32
print(x.dtype, x.device, x.element_size() * x.nelement() / 1e6, "MB")      # 67.1 MB
if torch.cuda.is_available():
    dev = torch.device("cuda:0")
    xg = x.to(dev, non_blocking=True)       # host-to-device copy (async only from pinned memory)
    y = xg @ xg                              # runs on the GPU asynchronously
    torch.cuda.synchronize()                 # wait for the GPU (needed for correct timing)
```

Key facts for infrastructure:

- **Asynchronous execution**: CUDA kernel launches return immediately; the CPU runs ahead until something forces a **synchronisation** (`.item()`, `.cpu()`, `print(tensor)`, `torch.cuda.synchronize()`, boolean checks on GPU tensors). Timing without synchronising measures only launch time. Accidental syncs inside the training loop (logging `loss.item()` every step) stall the pipeline.
- **Host-device transfers** cross PCIe (or NVLink-C2C on Grace Hopper); they are slow relative to on-device memory bandwidth. Use **pinned (page-locked) host memory** (`pin_memory=True` in DataLoader, `tensor.pin_memory()`) with `non_blocking=True` to overlap copies with compute. Move data to the GPU once, in large batches; keep intermediate results on the device.
- **dtypes**: `float32` is standard; `float16` and `bfloat16` halve memory and use Tensor Cores (bfloat16 keeps float32's exponent range and avoids most loss-scaling issues; supported on Ampere and later); `float8` on Hopper/Blackwell via Transformer Engine; `int8` for quantised inference. `torch.set_float32_matmul_precision("high")` allows TF32 on Ampere+ for faster matmuls at slightly lower precision.
- **Views and in-place ops**: `view/reshape/transpose/permute/expand` share storage; in-place ops (trailing underscore, `+=`) save memory but can break autograd if they overwrite a value needed for the backward pass.
- **Interop**: `torch.from_numpy(arr)` shares memory (CPU); `tensor.numpy()` shares memory for CPU tensors; GPU tensors must be `.cpu()` first. DLPack (`torch.utils.dlpack`) exchanges GPU tensors zero-copy with CuPy, JAX, RAPIDS.

### 3.2 Autograd and modules

**Autograd** records operations on tensors with `requires_grad=True` in a dynamic graph and `loss.backward()` computes gradients by reverse-mode differentiation, accumulating into `.grad`. `nn.Module` composes layers and tracks parameters; optimisers (`SGD`, `Adam`, `AdamW`) update parameters from gradients.

```python
import torch, torch.nn as nn, torch.nn.functional as F

class MLP(nn.Module):
    def __init__(self, d_in, d_hidden, d_out):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, d_hidden), nn.GELU(), nn.Linear(d_hidden, d_out))
    def forward(self, x): return self.net(x)

model = MLP(512, 2048, 10).to(dev)
opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)

for step, (xb, yb) in enumerate(loader):
    xb, yb = xb.to(dev, non_blocking=True), yb.to(dev, non_blocking=True)
    opt.zero_grad(set_to_none=True)                 # frees gradient memory instead of zero-filling
    loss = F.cross_entropy(model(xb), yb)
    loss.backward()                                  # builds gradients; frees the graph by default
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    if step % 100 == 0: print(step, loss.item())     # .item() synchronises: log sparingly
```

Mode switches: `model.train()` / `model.eval()` (dropout, batch norm behave differently); `torch.no_grad()` / `torch.inference_mode()` for evaluation and serving to skip graph building (saves memory and time). Forgetting `eval()` and `no_grad()` in validation is a frequent cause of OOM and wrong metrics. Retaining tensors that still carry graph history (appending `loss` rather than `loss.item()` to a list) keeps whole graphs alive and leaks memory step after step.

### 3.3 Where the memory goes

For training with Adam in mixed precision, per-parameter memory is roughly: weights (2 bytes in bf16, plus a 4-byte fp32 master copy), gradients (2 to 4 bytes), optimiser states (two fp32 moments: 8 bytes), so about **16 bytes per parameter** before activations; a 7-billion-parameter model needs roughly 112 GB of state, more than one 80 GB GPU, which is why sharding (FSDP/ZeRO) exists (Part 14). **Activations** scale with batch size, sequence length and depth, and are often the largest term; **activation (gradient) checkpointing** (`torch.utils.checkpoint`) trades about 30% extra compute for large memory savings. For inference, weights (2 bytes per parameter in fp16/bf16, 1 in int8, ~0.5 in 4-bit) plus the **KV cache**, which grows with batch size and context length, dominate (Part 15).

Allocator behaviour: PyTorch uses a **caching allocator**: freed blocks are retained for reuse, so `nvidia-smi` shows high usage even when tensors are freed, and **fragmentation** can cause OOM with free-but-unusable memory. Inspect with `torch.cuda.memory_allocated()` (live tensors), `memory_reserved()` (cached), `torch.cuda.memory_summary()`, `torch.cuda.memory._record_memory_history()` plus the memory snapshot visualiser; tune with `PYTORCH_CUDA_ALLOC_CONF` (for example `expandable_segments:True`, `max_split_size_mb`). `torch.cuda.empty_cache()` returns cached memory to the driver (rarely a real fix).

### 3.4 Mixed precision, accumulation and compilation

```python
scaler = torch.amp.GradScaler("cuda")                # needed for fp16; unnecessary for bf16
for xb, yb in loader:
    with torch.autocast("cuda", dtype=torch.bfloat16):          # ops run in lower precision where safe
        loss = F.cross_entropy(model(xb.to(dev)), yb.to(dev)) / accum
    loss.backward()                                  # with fp16 use scaler.scale(loss).backward()
    if (step + 1) % accum == 0:                      # gradient accumulation: effective batch = batch * accum
        opt.step(); opt.zero_grad(set_to_none=True)
```

`torch.compile(model)` (TorchInductor/Triton) fuses operations and reduces launch overhead and memory traffic, with compile-time cost, graph breaks to watch for, and recompilation on shape changes. `torch.backends.cudnn.benchmark = True` autotunes convolution algorithms for fixed shapes. Fused optimisers (`fused=True`) and flash attention (`F.scaled_dot_product_attention`) are standard speed-ups.

### 3.5 Data loading: usually the real bottleneck

`torch.utils.data.Dataset` defines `__len__`/`__getitem__`; `DataLoader` batches samples using worker **processes**.

```python
loader = torch.utils.data.DataLoader(
    ds, batch_size=64, shuffle=True,
    num_workers=8,                 # parallel decode/augment processes (fork or spawn; each has its own memory)
    pin_memory=True,               # page-locked buffers for fast async H2D copy
    persistent_workers=True,       # don't respawn workers every epoch
    prefetch_factor=4,             # batches prefetched per worker
    drop_last=True)
```

GPU starvation shows as low `nvidia-smi` utilisation with CPU workers at 100% or I/O wait high. Diagnose: time `next(iter(loader))` versus the model step; check CPU per core (`top`, `mpstat`), I/O (`iostat`, network file system throughput), and decoding cost (JPEG decode, tokenisation). Fixes: more workers (up to cores available, remembering BLAS thread oversubscription), faster formats (sharded Parquet/WebDataset, pre-tokenised memory-mapped arrays), caching/prefetching to local NVMe, GPU decoding (DALI, nvJPEG), larger sequential reads, avoiding Python-heavy per-sample transforms, and keeping dataset objects lightweight (large Python lists or dicts in the Dataset are copied-on-access in forked workers because reference counts touch pages: use NumPy arrays or Arrow tables). Seed workers explicitly for reproducibility (`worker_init_fn`, `generator`). In distributed training, `DistributedSampler` shards data across ranks and `set_epoch(epoch)` must be called each epoch to reshuffle.

### 3.6 Checkpointing and saving

```python
torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "step": step, "rng": torch.get_rng_state()}, tmp)
os.replace(tmp, "ckpt.pt")                  # atomic rename: never leave a half-written checkpoint
state = torch.load("ckpt.pt", map_location="cpu", weights_only=True)
```

- Save to a temp name and rename; write to fast local storage then upload asynchronously; keep the last N plus periodic milestones; record the code version, config and data position so a resume is exact.
- **Security**: `torch.load` uses pickle and can execute arbitrary code from an untrusted file; use `weights_only=True` (default in recent versions), or the **safetensors** format (safe, zero-copy, memory-mappable, fast) for model weights from anywhere you do not control.
- Large-model checkpoints are tens to hundreds of GB; sharded checkpoints (`torch.distributed.checkpoint`) save per-rank shards in parallel and support resharding on resume (Part 14).

## 4. Distributed and multi-GPU hooks (preview)

- `torch.distributed` provides process groups with backends NCCL (GPU, uses NVLink/InfiniBand/RoCE), Gloo (CPU), MPI; launched by `torchrun` (sets `RANK`, `WORLD_SIZE`, `LOCAL_RANK`, `MASTER_ADDR`, `MASTER_PORT`).
- **DistributedDataParallel (DDP)**: one process per GPU, model replicated, gradients all-reduced during backward (bucketed, overlapped with compute). **FSDP** shards parameters, gradients and optimiser states across ranks. Tensor/pipeline/sequence parallelism are in Megatron-LM, DeepSpeed and `torch.distributed.tensor`.
- Typical environment variables an infrastructure engineer sets: `NCCL_DEBUG=INFO`, `NCCL_SOCKET_IFNAME`, `NCCL_IB_HCA`, `NCCL_P2P_DISABLE` for diagnosis, `CUDA_VISIBLE_DEVICES`, `OMP_NUM_THREADS`, `TORCH_DISTRIBUTED_DEBUG=DETAIL`. All details are in Parts 12 and 14.

## 5. Profiling and observability of ML code

- **Wall clock first**: log step time, samples/s or tokens/s, data-wait time versus compute time. The ratio tells you whether the loader or the GPU is the bottleneck.
- **GPU metrics**: `nvidia-smi dmon`, DCGM (utilisation, SM activity, memory bandwidth, power, throttle reasons, NVLink). "Utilisation" in `nvidia-smi` only means a kernel was running during the sample, not that the GPU was efficient; use SM occupancy/Tensor Core activity and achieved model FLOPs utilisation (MFU) for a real picture.
- **PyTorch profiler**:

```python
from torch.profiler import profile, schedule, ProfilerActivity, tensorboard_trace_handler
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
             schedule=schedule(wait=1, warmup=1, active=3),
             on_trace_ready=tensorboard_trace_handler("./prof"),
             record_shapes=True, profile_memory=True, with_stack=True) as prof:
    for step, batch in zip(range(6), loader):
        train_step(batch); prof.step()
print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=15))
```

  Inspect kernel timelines (gaps between kernels mean CPU-bound or data-starved), top operators, memory usage, and communication ops. NVIDIA **Nsight Systems** (`nsys profile`) shows the whole pipeline (CPU threads, CUDA API, kernels, NCCL, NVTX ranges; add `torch.cuda.nvtx.range_push/pop` markers) and **Nsight Compute** drills into single kernels (Part 10).
- **CPU side**: `py-spy` on training processes (is the main thread in the dataloader, in Python overhead, or waiting on a sync?), `perf`, and `top -H` to see worker threads.
- **Experiment tracking** (Weights & Biases, MLflow, TensorBoard) records metrics, configs, code versions and artefacts so runs are reproducible and comparable (Part 16).
- **Health signals**: loss NaN/Inf detection, gradient norm logging, per-rank step-time skew (stragglers), GPU XID errors in `dmesg`, ECC counters, and heartbeat/timeouts so a hung collective is detected instead of burning GPU-hours.

## 6. Reproducibility and determinism

Runs differ because of random seeds (Python, NumPy, PyTorch CPU and CUDA, data order, worker seeds), non-deterministic GPU kernels (atomic adds in some backward ops), changing library versions, different numbers of GPUs, reduction order and cuDNN autotuning.

```python
import random, numpy as np, torch
def seed_everything(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)
seed_everything(1234)
torch.use_deterministic_algorithms(True, warn_only=True)     # raises/warns on non-deterministic ops
torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
# also set CUBLAS_WORKSPACE_CONFIG=:4096:8 for deterministic cuBLAS
```

Determinism costs speed; use it for debugging and regression tests, not necessarily for production training. Record exact versions (`pip freeze`, CUDA, driver, NCCL, container digest) with each run; bitwise reproducibility across different GPU counts is generally not achievable.

## 7. Packaging and environments for ML code

- **Wheels vs CUDA**: PyTorch wheels bundle CUDA runtime libraries; choose the index URL matching the CUDA version (`--index-url https://download.pytorch.org/whl/cu1xx`), and ensure the **driver** is new enough for that CUDA (driver supports older runtimes; not vice versa; see Part 10). Mixed CUDA versions between PyTorch, NCCL, and custom extensions cause confusing import errors.
- **Containers**: use NVIDIA NGC PyTorch containers (curated CUDA, cuDNN, NCCL, Transformer Engine versions) or build on `nvidia/cuda` base images; run with the NVIDIA Container Toolkit (`--gpus all`) (Part 11).
- **Dependency pinning** with lock files (uv, pip-tools, poetry) and a recorded container digest; ML stacks break easily on minor-version bumps (numpy 2 ABI changes, transformers/torch compatibility).
- **Virtual environments per project**; avoid `pip install` into system Python; conda/mamba remain common for CUDA toolkits and native deps.
- **Large files** (datasets, checkpoints) do not belong in Git: DVC, git-lfs, object storage with content addressing, model registries (Part 16).

## 8. Common failure modes

| Symptom | Likely cause | Check |
|---|---|---|
| `CUDA out of memory` | batch/sequence too large, retained graphs, fragmentation, other processes on the GPU | `torch.cuda.memory_summary()`, `nvidia-smi`, reduce batch, checkpointing, `expandable_segments`, `torch.no_grad()` in eval |
| Low GPU utilisation, high CPU | data loading or Python overhead | profile loader time, add workers, faster format, pin memory, `torch.compile`/CUDA graphs |
| Memory grows every step | storing tensors with graph (`losses.append(loss)`), growing lists/caches | store `.item()`/`.detach()`, `tracemalloc` and `torch.cuda.memory_allocated` over time |
| Loss becomes NaN | learning rate too high, fp16 overflow, bad data, division by zero | anomaly detection `torch.autograd.set_detect_anomaly(True)` (slow), gradient clipping, bf16, data validation |
| Training slower with more workers | BLAS/OMP thread oversubscription, shared-memory limits | set `OMP_NUM_THREADS=1` per worker, check `/dev/shm` size in containers (set larger `--shm-size`) |
| `DataLoader worker killed` / bus error | `/dev/shm` too small in Docker/Kubernetes, or host RAM OOM | enlarge shm (emptyDir medium Memory), reduce workers/prefetch |
| Hangs at start of multi-GPU run | rendezvous misconfig, NCCL network interface wrong, firewall | `NCCL_DEBUG=INFO`, `NCCL_SOCKET_IFNAME`, check ports and `MASTER_ADDR` |
| Different results run to run | nondeterministic kernels, unseeded workers | section 6 |
| Slow first step, then fast | lazy init, cudnn benchmark, `torch.compile` warm-up | warm up before timing; synchronise before measuring |
| Pandas job killed | OOM from copies and object dtype | dtypes, chunking, Parquet column pruning, Polars/DuckDB |

## 9. Lab (untested)

1. **NumPy model**: create arrays and print `shape/strides/dtype`; demonstrate a view mutation bug; compare a Python loop, a list comprehension and a vectorised version of pairwise distances (time with `%timeit`/`timeit`); show quadratic `np.concatenate` in a loop versus preallocation; map a large `.npy` with `mmap_mode` and read it from two processes.
2. **Thread oversubscription**: time a matrix multiply with `OMP_NUM_THREADS` of 1, 4 and all cores; spawn 8 worker processes each using all BLAS threads and observe the slowdown; fix with `threadpoolctl`.
3. **pandas diet**: generate a 5 million row CSV; load with defaults and with narrow dtypes/categories/usecols; compare memory and time; write Parquet (zstd) and compare size and column-pruned read time; repeat the groupby in Polars and DuckDB.
4. **Tensors and devices**: reproduce the async illusion: time a GPU matmul with and without `torch.cuda.synchronize()`; measure pageable vs pinned host-to-device bandwidth; show an accidental `.item()` sync in a loop.
5. **Training loop**: implement the MLP loop on synthetic data; toggle `train/eval`, `no_grad`; deliberately leak by appending `loss`, graph-retaining, and watch memory grow; fix.
6. **Memory accounting**: for a small transformer from `torch.nn`, predict memory (weights, grads, Adam state, activations) and compare with `torch.cuda.max_memory_allocated()`; enable bf16 autocast, then activation checkpointing, and record each effect.
7. **Data loader tuning**: build a Dataset with an artificial 20 ms per-sample decode; measure samples/s for `num_workers` of 0, 2, 4, 8, `pin_memory`, `persistent_workers`; find where GPU utilisation saturates; reproduce the `/dev/shm` failure in a container with a small `--shm-size`.
8. **Profiler**: capture a PyTorch profiler trace of the loop, open it in TensorBoard/Perfetto, identify the largest gaps and operators; run `nsys profile` and add NVTX ranges.
9. **Checkpoint safety**: save with temp-and-rename; kill the process during a save and confirm the previous checkpoint remains valid; load with `weights_only=True`; convert to safetensors and compare load time with `mmap`.
10. **Determinism**: run twice unseeded then seeded; enable deterministic algorithms and measure the speed cost; locate a non-deterministic op that warns.
11. **Packaging**: build a CUDA-matched virtual environment and a container from an NGC image; verify `torch.cuda.is_available()`, driver/runtime versions, and `python -c "import torch; print(torch.__config__.show())"`.
12. **Clean up.**

Mark tested only after execution.

## 10. Interview angles

- "Training is slow and GPU utilisation is 40%. Walk me through diagnosis." (loader vs compute vs sync; profiler; storage; threads.)
- "Why does GPU memory show used after you delete tensors?" (caching allocator; reserved vs allocated.)
- "What takes memory during training? How would you fit a bigger model?" (state per parameter, activations, mixed precision, checkpointing, sharding, offload.)
- "Explain views versus copies and broadcasting pitfalls."
- "How do you make a PyTorch job reproducible? What does it cost?"
- "Why is `torch.load` on an untrusted file dangerous? What do you use instead?"
- "pandas ran out of memory on a 30 GB CSV on a 32 GB machine. Options?" (dtypes, chunks, Parquet, Polars/DuckDB, Dask.)
- "What does `num_workers`, `pin_memory`, and `persistent_workers` do?"
- "Why can `/dev/shm` be a problem for DataLoader in Kubernetes?"

## 11. Checkpoint questions (35)

1. What three things define an ndarray's layout? **A:** dtype, shape, strides.
2. Is a transpose a copy? **A:** No, a view with swapped strides.
3. How much memory is a billion float32 values? **A:** About 4 GB.
4. What is broadcasting? **A:** Virtually stretching size-1 axes to match shapes.
5. Why vectorise? **A:** Loops run in C/SIMD/BLAS, far faster.
6. What controls BLAS threads? **A:** `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`.
7. Why memory-map large arrays? **A:** Share via page cache without loading fully.
8. How to cut pandas memory? **A:** Narrow dtypes, categoricals, usecols, chunks, Arrow dtypes.
9. Why avoid `iterrows`? **A:** Slow Python-level loop.
10. What does Parquet give over CSV? **A:** Columnar compression, column pruning, predicate pushdown.
11. What is Arrow? **A:** In-memory columnar format enabling zero-copy exchange.
12. When Polars/DuckDB over pandas? **A:** Larger data, multi-core, lazy/SQL workloads.
13. What is cuDF? **A:** GPU dataframe library in RAPIDS.
14. What attributes does a tensor add to an array? **A:** Device and autograd metadata.
15. Why is CUDA asynchronous important for timing? **A:** Must synchronise to measure real compute.
16. Name operations that synchronise. **A:** `.item()`, `.cpu()`, printing, `synchronize()`.
17. Why pinned memory? **A:** Faster, async host-to-device copies.
18. bf16 versus fp16? **A:** bf16 has fp32 range, no loss scaling needed.
19. What does `zero_grad(set_to_none=True)` do? **A:** Frees gradient tensors instead of zero-filling.
20. What does `no_grad` / `inference_mode` do? **A:** Disables graph building, saving memory/time.
21. Why does appending `loss` leak memory? **A:** Keeps the autograd graph alive.
22. Per-parameter training memory with Adam mixed precision? **A:** About 16 bytes.
23. What is activation checkpointing? **A:** Recompute activations in backward to save memory.
24. What is `memory_reserved` vs `memory_allocated`? **A:** Cached by allocator vs live tensors.
25. Why is `empty_cache()` rarely a fix? **A:** Doesn't free live memory; fragmentation needs other fixes.
26. What do DataLoader workers do? **A:** Parallel processes loading and preprocessing batches.
27. Symptom of data starvation? **A:** Low GPU utilisation, busy CPU or I/O.
28. Why can big Python lists in a Dataset hurt workers? **A:** Copy-on-access from reference counting in forked processes.
29. Why call `sampler.set_epoch`? **A:** Reshuffle differently each epoch in distributed training.
30. Safe checkpoint write pattern? **A:** Temp file then atomic rename.
31. Why distrust `torch.load` of unknown files? **A:** Pickle can execute code; use `weights_only` or safetensors.
32. What launches multi-GPU jobs? **A:** `torchrun`.
33. DDP vs FSDP? **A:** Replicate model with gradient all-reduce vs shard params/grads/optimiser.
34. What does MFU mean? **A:** Model FLOPs utilisation versus peak hardware FLOPs.
35. Why enlarge `/dev/shm` in containers? **A:** DataLoader uses shared memory for batches; small shm kills workers.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Chip Huyen, *AI Engineering* (compute and memory arithmetic, inference and training bottlenecks, evaluation and monitoring concerns) and *Designing Machine Learning Systems* (data formats, feature leakage, training data pipelines, reproducibility, deployment and monitoring).
- NumPy, pandas, Apache Arrow/Parquet, Polars, DuckDB and PyTorch documentation (autograd, DataLoader, AMP, profiler, CUDA semantics, reproducibility notes, distributed overview) and NVIDIA Nsight and NGC documentation.
- Examples and memory arithmetic are the author's constructions; the 16 bytes per parameter figure is a common rule of thumb for Adam with mixed precision and varies by implementation.

**Flagged for verification before publishing:** PyTorch API names and defaults across versions (`weights_only` default, `GradScaler` namespace, `torch.compile` behaviour, allocator config options), pandas copy-on-write and Arrow dtype status, CUDA index URLs, cuDNN/cuBLAS determinism settings, memory rules of thumb, and every code listing; all labs are **untested**.
