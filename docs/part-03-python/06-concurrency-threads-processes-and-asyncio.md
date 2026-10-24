---
id: "c03-06"
title: "3.6 Concurrency: threads, processes and asyncio"
sidebar_label: "3.6 Concurrency: threads, processes and asyncio"
sidebar_position: 6
description: "Concurrency models in Python: the GIL, threads and executors, multiprocessing, asyncio, backpressure, timeouts and cancellation, choosing the model, and operational patterns for infrastructure fan-out"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "Mac"
---

# 3.6 Concurrency: threads, processes and asyncio

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | Any machine with Python 3.11+, several cores, optionally a fleet of test endpoints (local mock servers) |
| Part | Part 3: Python for infrastructure |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Infrastructure work is fan-out: query 5,000 BMCs, health-check 800 nodes, upload 10 million objects, tail logs from every pod, pre-process shards of a dataset, serve many inference requests while a model runs. Doing it sequentially is too slow; doing it concurrently without understanding the model produces hangs, resource exhaustion, race conditions and runaway memory. Python offers three concurrency models (threads, processes, asyncio) with different costs and the Global Interpreter Lock (GIL) shaping which one fits which workload. This chapter explains the models from first principles, shows how to choose, and covers the production patterns that matter: bounded concurrency, backpressure, timeouts, cancellation, error aggregation, retries, graceful shutdown, and diagnosing hangs. It prepares the ground for FastAPI services (3.7), exporters and agents (3.8) and data pipelines (3.10).

## Prerequisites and outcomes

You should know functions, generators and classes (3.1 to 3.4) and subprocess/signal basics (3.5).

After this chapter you can:

- Distinguish concurrency from parallelism; I/O-bound from CPU-bound work; explain the GIL, what it protects, when it is released, and the status of free-threaded builds and subinterpreters.
- Use `threading` (Thread, Lock, RLock, Event, Condition, Semaphore, Queue), `concurrent.futures` (`ThreadPoolExecutor`, `ProcessPoolExecutor`), and `multiprocessing` (Process, Pool, Queue, shared memory), with correct synchronisation and cleanup.
- Write `asyncio` code: coroutines, tasks, `gather`, `TaskGroup`, `wait_for`/`timeout`, semaphores, queues, cancellation, async context managers and iterators, async HTTP and subprocess; integrate blocking code via `to_thread`/executors; avoid blocking the event loop.
- Choose the model for a workload, size pools, and implement backpressure with bounded queues.
- Recognise and avoid data races, deadlocks, livelocks, starvation, thundering herds, fork-safety issues and orphaned work.
- Aggregate results and errors from many concurrent operations; implement retries with jitter, circuit breakers and rate limits; shut down gracefully.
- Profile and debug concurrency problems (faulthandler, py-spy, asyncio debug mode).

## 1. Concepts

- **Concurrency**: structuring a program so multiple tasks make progress in overlapping time periods (dealing with many things at once). **Parallelism**: executing multiple computations simultaneously on multiple cores (doing many things at once). You can have concurrency without parallelism (one core interleaving tasks).
- **I/O-bound** work spends time waiting (network, disk, subprocesses, sleeping): concurrency helps even on one core because waiting overlaps. **CPU-bound** work spends time computing: only parallelism across cores (or faster code, native libraries) helps.
- **Latency vs throughput**; **Amdahl's law**: speed-up is limited by the serial fraction. Overheads (thread creation, context switches, serialisation between processes) can exceed gains for small tasks.
- **Shared state is the enemy**: the more tasks share mutable data, the more locks, races and bugs. Prefer **message passing** (queues), immutable data, and per-task state.

### The Global Interpreter Lock

CPython's reference implementation has a **GIL**: a mutex ensuring only one thread executes Python bytecode at a time within a process. It simplifies memory management (reference counting is not thread-safe without it) and the implementation of C extensions. Consequences:

- **Threads do not speed up pure-Python CPU-bound code**; they can slow it down (contention, switching).
- **The GIL is released** during blocking I/O (`socket`, file reads, `time.sleep`, `subprocess` waits), and by many C extensions during long computations (NumPy, hashlib on large buffers, compression, regex in some cases, PyTorch ops, `zlib`), so threads *do* give speed-ups for I/O-bound code and for native-code-heavy work.
- Individual bytecode operations are atomic-ish, but compound operations (`x += 1`, check-then-act on a dict) are **not** thread-safe: races still occur. The GIL does not remove the need for locks.
- Since 3.2 the interpreter switches threads on a time slice (`sys.getswitchinterval()`, 5 ms default).
- **Free-threaded CPython** (PEP 703): optional builds (3.13+ experimental `python3.13t`, supported builds in later releases) run without the GIL; extension compatibility and single-thread overhead are evolving; check each dependency. **Subinterpreters** (PEP 684/734, `concurrent.interpreters` in 3.14) give per-interpreter GILs. Treat both as emerging; the models below remain the practical toolkit.
- Alternative implementations/approaches: processes (separate GILs), native extensions (Cython, Numba, Rust via PyO3), vectorised libraries (NumPy, pandas, PyTorch) that spend time outside the interpreter.

### Choosing a model

| Workload | Best fit | Why |
|---|---|---|
| Many network calls / API polls / SSH sessions (hundreds to thousands) | **asyncio** (with async libraries), or threads (simpler with blocking libraries) | Waiting dominates; lightweight tasks |
| Moderate fan-out with blocking libraries (`requests`, `paramiko`, `boto3`) | **ThreadPoolExecutor** | Easy; GIL released on I/O; pool size 10 to 200 |
| CPU-bound pure Python (parsing, hashing many small items, simulation) | **ProcessPoolExecutor / multiprocessing** | Separate GIL per process; use cores |
| CPU-bound numeric | NumPy/pandas/PyTorch/Numba (vectorised, releases GIL) or processes | Native speed |
| Mixed: async server + blocking calls / CPU work | asyncio + `to_thread` / process pool | Keep the loop free |
| Long-running background work in a web service | Task queues (Celery, RQ, Dramatiq, Arq, Kubernetes Jobs) | Isolation, retries, scaling |
| Distributed compute across nodes | Ray, Dask, MPI (`mpi4py`), Slurm arrays, Kubernetes | Beyond one machine |
| Simple one-off parallelism | Shell (`xargs -P`, GNU `parallel`) | Sometimes the right answer |

A common sizing heuristic: threads for I/O = (expected concurrency of the remote system you can tolerate) rather than "as many as possible"; processes for CPU = number of cores (`os.cpu_count()` / `len(os.sched_getaffinity(0))`, or the cgroup CPU limit in containers); asyncio concurrency limited by a semaphore to what the target and your sockets can sustain. Always apply **bounded concurrency**: unbounded fan-out overwhelms targets (a thundering herd on a BMC network or an API) and your own file descriptors and memory.

## 2. Threads

### Basics

```python
import threading, time

def worker(name, delay):
    time.sleep(delay)                              # releases the GIL
    print(f"{name} done")

threads = [threading.Thread(target=worker, args=(f"t{i}", 1), name=f"worker-{i}", daemon=True) for i in range(5)]
for t in threads: t.start()
for t in threads: t.join(timeout=10)               # wait; join with timeout so you can detect stuck threads
print(threading.active_count(), threading.current_thread().name)
```

- **Daemon threads** are killed abruptly at interpreter exit (no cleanup): use them only for background chores that can be dropped. Non-daemon threads keep the process alive until they finish.
- **Exceptions in threads** don't propagate to the main thread: they print a traceback and the thread ends. Capture them (use executors/futures) or set `threading.excepthook`.
- There is **no way to kill a thread** from outside. Design cooperative cancellation with a `threading.Event` that workers check, and time-bounded blocking calls (socket timeouts, queue `get(timeout=)`).
- `threading.local()` for thread-local state; `contextvars` for context that follows tasks/threads.

### Synchronisation primitives

| Primitive | Purpose |
|---|---|
| `Lock` | Mutual exclusion; use `with lock:` |
| `RLock` | Re-entrant lock (same thread may acquire repeatedly) |
| `Event` | One-bit flag: `set`, `clear`, `wait(timeout)`; shutdown signals |
| `Condition` | Wait for a condition under a lock; `notify`, `wait_for(predicate)` |
| `Semaphore` / `BoundedSemaphore` | Limit concurrent access to N resources (connection limits) |
| `Barrier` | Rendezvous N threads |
| `Timer` | Run a function after a delay |
| `queue.Queue` / `LifoQueue` / `PriorityQueue` / `SimpleQueue` | Thread-safe FIFO/LIFO/priority; `maxsize` bounds; `task_done`/`join` |

```python
import threading
counter = 0
lock = threading.Lock()
def incr(n):
    global counter
    for _ in range(n):
        with lock:                    # without the lock, 'counter += 1' (load, add, store) can lose updates
            counter += 1
```

**Data races** (lost updates, torn invariants), **deadlock** (two threads each hold a lock the other needs; avoid by a global lock order, acquiring with timeouts, or holding at most one lock), **livelock**, **starvation**, **priority inversion**. Rules: keep critical sections tiny and free of I/O; never call unknown callbacks while holding a lock; prefer queues and immutable messages over shared mutable data; test with stress loops.

### Producer/consumer with a bounded queue

```python
import queue, threading

q: queue.Queue = queue.Queue(maxsize=100)          # bounded: put() blocks when full = backpressure
SENTINEL = object()

def producer(items):
    for it in items:
        q.put(it)                                   # blocks if consumers are slower
    for _ in range(N_CONSUMERS):
        q.put(SENTINEL)

def consumer():
    while (item := q.get()) is not SENTINEL:
        try: handle(item)
        finally: q.task_done()
```

### `concurrent.futures`

The high-level API for pools: submit callables, get `Future` objects.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_EXCEPTION
import requests

def check(host):
    r = requests.get(f"https://{host}/healthz", timeout=5)
    return host, r.status_code

hosts = [...]
results, errors = {}, {}
with ThreadPoolExecutor(max_workers=50, thread_name_prefix="probe") as pool:
    futs = {pool.submit(check, h): h for h in hosts}
    for fut in as_completed(futs, timeout=120):                 # yields as each completes; overall deadline
        h = futs[fut]
        try:
            results[h] = fut.result()[1]                          # re-raises the worker's exception here
        except Exception as exc:
            errors[h] = repr(exc)
print(len(results), "ok;", len(errors), "failed")
```

- `pool.map(fn, iterable, timeout=..)` returns results in input order and raises the first exception when iterated; `as_completed` handles results out of order and per-future errors; `wait(futs, return_when=FIRST_EXCEPTION)` for fail-fast.
- `Future.result(timeout)`, `.exception()`, `.cancel()` (only if not started), `.add_done_callback()`, `.done()`.
- Leaving the `with` block waits for all pending work (`shutdown(wait=True)`); on exceptions `shutdown(wait=False, cancel_futures=True)` (3.9+) drops queued tasks.
- Executors **do not interrupt running tasks** on timeout: always set timeouts on the I/O inside the task.

### Backpressure with executors (avoiding the "10 million futures" OOM)

`for x in huge_iterable: pool.submit(...)` creates all futures immediately and holds them; memory explodes before work begins. Feed the pool in a bounded way:

```python
from itertools import islice
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

def bounded_map(fn, iterable, *, workers=50, max_inflight=200):
    it = iter(iterable)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        inflight = {pool.submit(fn, x) for x in islice(it, max_inflight)}
        while inflight:
            done, inflight = wait(inflight, return_when=FIRST_COMPLETED)
            for fut in done:
                yield fut.result()                            # or handle errors here
            for x in islice(it, len(done)):                    # refill to keep max_inflight outstanding
                inflight.add(pool.submit(fn, x))
```

This keeps memory O(max_inflight) regardless of input size (a classic production fix for S3 listing/copy jobs and fleet-wide commands).

### Thread safety of common objects

`queue.Queue`, `logging`, `list.append`/`pop` (atomic operations), `dict` single operations are safe; compound operations are not. Many third-party clients are **not thread-safe** (a `requests.Session` is mostly safe for reads but share carefully; `paramiko` clients, database connections, `boto3` clients are generally safe for concurrent use while `boto3` *sessions*/resources are not; check documentation) — create one client per thread (thread-local) when in doubt. SQLite connections are per-thread by default.

## 3. Processes

### `multiprocessing` and `ProcessPoolExecutor`

```python
from concurrent.futures import ProcessPoolExecutor
import os, hashlib

def sha(path):                       # must be a top-level function: arguments and results are pickled
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return path, h.hexdigest()

if __name__ == "__main__":           # REQUIRED on spawn platforms (macOS, Windows, and default in 3.14 on Linux): guards re-import
    files = [...]
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
        for path, digest in pool.map(sha, files, chunksize=16):          # chunksize batches IPC for many small tasks
            print(digest, path)
```

- **Start methods**: `fork` (copy-on-write child, fast, but unsafe with threads, locks held at fork time, CUDA contexts, open sockets; the default on Linux until 3.13/3.14), `spawn` (fresh interpreter importing your module; safe, slower, requires picklable arguments and `if __name__ == "__main__"`), `forkserver` (a clean server process forks workers). Select with `multiprocessing.set_start_method("spawn")` or `mp_context=multiprocessing.get_context("forkserver")`. **Never use `fork` after initialising CUDA** (PyTorch DataLoader workers and distributed launchers use `spawn`/`forkserver` for this reason); also avoid forking a process with running threads or gRPC/OpenMP state.
- **Pickling**: arguments and return values cross process boundaries via pickle; lambdas, nested functions, open files, sockets and locks can't be pickled (use top-level functions and plain data); large objects are copied (slow): pass file paths/indices or use shared memory.
- **Sharing data**: `multiprocessing.Queue/Pipe/Manager`, `Value`/`Array` (ctypes, with locks), **`multiprocessing.shared_memory.SharedMemory`** (zero-copy buffers; the basis for NumPy arrays shared across processes), memory-mapped files (`numpy.memmap`), `fork` copy-on-write for read-only data (beware reference-count writes that trigger page copies: `gc.freeze()` helps).
- **Pools**: `multiprocessing.Pool(processes)` with `map`, `imap_unordered`, `apply_async`, `starmap`; `maxtasksperchild` to recycle leaky workers; `initializer` to set up per-worker state (open a model, DB connection).
- **Overheads**: process start time (tens of ms, plus imports), IPC serialisation, memory duplication. Use chunking, long-lived workers, and coarse-grained tasks.
- **Error handling**: exceptions in workers re-raise in the parent (traceback text attached); a worker killed by the OOM killer raises `BrokenProcessPool`; handle and restart; set resource limits.
- **Signals and cleanup**: children inherit signal handlers under fork; handle `SIGTERM` in the parent to terminate children (`pool.terminate()`); orphaned workers when the parent is `SIGKILL`ed need `prctl(PR_SET_PDEATHSIG)` or a supervisor (systemd, Kubernetes) to clean them up; use `daemon=True` carefully.
- **Containers and cgroups**: `os.cpu_count()` reports host CPUs, not the container's CPU limit; use `len(os.sched_getaffinity(0))` or read cgroup `cpu.max`; oversubscribing a CPU-limited container causes throttling (visible in `cpu.stat`).

### GPUs and data loading

PyTorch's `DataLoader(num_workers=N)` uses worker processes for decoding/augmentation; tune `num_workers`, `prefetch_factor`, `pin_memory`, `persistent_workers`, avoid fork-after-CUDA, and watch memory duplication; for training launchers (`torchrun`, `accelerate`, `deepspeed`, `mpirun`, Slurm `srun`) each GPU gets its own process: concurrency models here are process-per-GPU, with NCCL for communication (Part 14). Multi-threading within a rank is for I/O (prefetch threads), not compute.

## 4. asyncio

### Why asyncio

Threads are heavy (each has a stack, kernel scheduling) and limited to thousands; asyncio runs **many tasks cooperatively on one thread** using an **event loop** and non-blocking I/O (epoll/kqueue). A task runs until it hits an `await` on something that isn't ready, then yields control, so tens of thousands of concurrent connections cost little. Costs: all code on the loop must be non-blocking, libraries must be async-aware, and CPU-bound or blocking calls stall every task.

### Core concepts

```python
import asyncio, time

async def fetch(session, host):                   # coroutine function: calling it returns a coroutine object (does not run yet)
    async with session.get(f"https://{host}/healthz", timeout=5) as r:      # aiohttp / httpx.AsyncClient
        return host, r.status

async def main(hosts):
    sem = asyncio.Semaphore(100)                  # bounded concurrency
    async with aiohttp.ClientSession() as session:
        async def bounded(h):
            async with sem:
                try:
                    return await asyncio.wait_for(fetch(session, h), timeout=10)
                except Exception as exc:
                    return h, repr(exc)
        return await asyncio.gather(*(bounded(h) for h in hosts))
results = asyncio.run(main(hosts))                # creates the loop, runs main, closes the loop
```

- **Coroutine**: `async def` function; `await` suspends it until the awaited coroutine/Future/Task completes. `await` is only allowed inside `async def`.
- **Task**: `asyncio.create_task(coro)` schedules a coroutine to run concurrently; keep a reference (the loop holds only weak references; a dropped task can be garbage collected mid-flight). Tasks can be awaited, cancelled, and inspected.
- **Event loop**: single-threaded scheduler; `asyncio.run()` is the entry point; avoid `get_event_loop()` outside running contexts.
- **`gather(*aws, return_exceptions=True)`** runs awaitables concurrently and collects results (with `return_exceptions=False`, the first exception propagates but others keep running); **`TaskGroup`** (3.11) provides structured concurrency: tasks started in the group are awaited on exit; if one fails, the others are cancelled and an `ExceptionGroup` is raised.

```python
async def poll_all(nodes):
    results = {}
    try:
        async with asyncio.TaskGroup() as tg:                  # structured concurrency
            for n in nodes:
                tg.create_task(poll(n, results))
    except* TimeoutError as eg:
        log.error("timeouts: %s", [str(e) for e in eg.exceptions])
    return results
```

- **Timeouts**: `await asyncio.wait_for(coro, timeout)` or the `async with asyncio.timeout(10):` context (3.11). **Every network await must have a timeout** (the classic silent hang: a half-open connection waits forever).
- **Cancellation**: `task.cancel()` raises `asyncio.CancelledError` at the task's current `await`; clean up in `finally`, **re-raise `CancelledError`** (never swallow it), and use `asyncio.shield()` to protect critical sections. Timeouts and `TaskGroup` rely on cancellation.
- **Synchronisation**: `asyncio.Lock`, `Semaphore`, `Event`, `Condition`, `Queue` (bounded with `maxsize`: `await q.put()` provides backpressure) — async versions; not thread-safe across threads.
- **Async iteration/context managers**: `async for` over `__aiter__/__anext__` (streams, paginated APIs, async generators with `async def` + `yield`), `async with` for resources (`__aenter__/__aexit__`, `contextlib.asynccontextmanager`).
- **Subprocesses**: `asyncio.create_subprocess_exec(*cmd, stdout=PIPE)`, `await proc.communicate()`: non-blocking command execution, no pipe deadlocks if you read both streams (communicate does).
- **Blocking calls**: `await asyncio.to_thread(blocking_fn, args)` (3.9+) or `loop.run_in_executor(executor, fn, *args)` run blocking/CPU code off the loop. For CPU-bound work use a `ProcessPoolExecutor` via `run_in_executor`.
- **Async libraries**: `aiohttp`, `httpx.AsyncClient`, `asyncssh`, `aiofiles` (threads under the hood), `asyncpg`, `aioredis/redis.asyncio`, `aiokafka`, `kubernetes_asyncio`, `aioboto3`/`aiobotocore`, `grpc.aio`. Mixing sync libraries (requests, paramiko, boto3) inside coroutines blocks the loop: wrap with `to_thread`.
- **Debugging**: `asyncio.run(main(), debug=True)` or `PYTHONASYNCIODEBUG=1` logs slow callbacks (>100 ms), un-awaited coroutines ("coroutine ... was never awaited" warnings), and tasks destroyed while pending; `loop.slow_callback_duration`; `asyncio.all_tasks()` and `task.print_stack()` to see where tasks are stuck; `py-spy dump --pid` shows blocked loop stacks.
- **Event loop implementations**: `uvloop` (drop-in faster loop on Linux/macOS) improves throughput for servers.
- **Windows/macOS differences** exist (selector vs proactor); production Linux is the norm.

### A worker-pool template

```python
import asyncio, logging, random, signal
log = logging.getLogger("pool")

async def worker(name, q: asyncio.Queue, results: list, handler):
    while True:
        item = await q.get()
        try:
            results.append(await asyncio.wait_for(handler(item), timeout=30))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.warning("%s failed on %r: %r", name, item, exc)
            results.append(exc)
        finally:
            q.task_done()

async def run_pool(items, handler, concurrency=50, queue_size=500):
    q: asyncio.Queue = asyncio.Queue(maxsize=queue_size)       # bounded: producer awaits when workers lag
    results: list = []
    workers = [asyncio.create_task(worker(f"w{i}", q, results, handler)) for i in range(concurrency)]
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    try:
        for it in items:                                        # works with a (sync) generator of any length
            if stop.is_set(): break
            await q.put(it)
        await q.join()                                          # wait until all queued items are processed
    finally:
        for w in workers: w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
    return results
```

Properties: bounded memory, bounded concurrency, per-item timeouts and error isolation, clean cancellation on signals.

## 5. Patterns for infrastructure fan-out

### Retries, backoff and jitter

Retry only idempotent operations and transient errors (timeouts, connection resets, 429/503); use exponential backoff with **full jitter** to avoid synchronised retry storms; cap total time; honour `Retry-After`; log attempts.

```python
async def retry(fn, *, attempts=5, base=0.5, cap=20.0, retry_on=(asyncio.TimeoutError, ConnectionError)):
    for i in range(attempts):
        try:
            return await fn()
        except retry_on as exc:
            if i == attempts - 1: raise
            delay = random.uniform(0, min(cap, base * 2 ** i))            # full jitter
            await asyncio.sleep(delay)
```

Libraries: `tenacity`, `backoff`; HTTP clients have retry adapters (`urllib3.util.Retry` with `requests.adapters.HTTPAdapter`).

### Rate limiting and circuit breaking

Protect targets and yourself: token bucket (`aiolimiter`, `asyncio` semaphore + sleep), per-host concurrency limits (a semaphore per host/rack/BMC network), circuit breaker (stop calling a failing dependency for a cool-down), `Retry-After` handling, adaptive concurrency (AIMD like TCP). For BMC/Redfish fleets limit per-rack concurrency to avoid overwhelming management switches.

### Aggregating results

Return structured results per item (`Result(host, ok, value|error, duration)`), summarise at the end (success/failure counts, slowest, error classes), exit non-zero if any critical failure, and keep raw errors for diagnosis. Avoid letting one exception abort everything unless intended (use `return_exceptions=True` or catch inside the worker).

### Streaming and pagination

Combine async generators with queues for pipelines: `async for page in client.list_pages(): await q.put(page)`; consumers process in parallel with bounded concurrency; memory stays flat.

### Scheduling and periodic tasks

A simple periodic loop: `while not stop.is_set(): await run_once(); await asyncio.wait_for(stop.wait(), timeout=interval)` (interruptible sleep). Use `time.monotonic()` for drift-free intervals; for cron-like needs prefer systemd timers, Kubernetes CronJobs, or APScheduler; avoid `sleep` drift by computing the next deadline.

### Combining models

- **asyncio + processes**: `await loop.run_in_executor(process_pool, cpu_fn, data)`.
- **Threads + asyncio**: `asyncio.run_coroutine_threadsafe(coro, loop)` to submit from threads; `loop.call_soon_threadsafe` to touch the loop.
- **Multiprocess web servers**: gunicorn/uvicorn workers (one event loop per process) scale across cores; share state via external stores (Redis), not memory.
- **Background tasks in services**: FastAPI `BackgroundTasks` for short fire-and-forget; real queues for durable work (chapter 3.7).

### Distributed concurrency

When one machine isn't enough: Slurm job arrays and `srun`, Kubernetes Jobs with `completions`/`parallelism` and indexed jobs, Ray remote functions/actors, Dask, Celery/RQ workers. Idempotency, checkpointing and at-least-once semantics matter more than the in-process model.

## 6. Pitfalls and diagnosis

| Problem | Symptom | Cause / remedy |
|---|---|---|
| Blocking the event loop | Tasks stall, timeouts everywhere, loop "slow callback" warnings | Sync I/O (`requests`, `time.sleep`, subprocess.run, heavy CPU) in a coroutine: use async APIs or `to_thread` |
| Un-awaited coroutine | Work never happens; "was never awaited" warning | Forgot `await`/`create_task` |
| Dropped task reference | Tasks vanish or exceptions never seen ("Task exception was never retrieved") | Keep references; await or add done callbacks |
| Swallowed `CancelledError` | Cannot cancel/shutdown | Re-raise it; don't use bare `except` |
| Missing timeouts | Hangs after network blips | `wait_for`/`timeout` on every await; socket timeouts; `timeout=` in clients |
| Unbounded fan-out | OOM, too many open files, target overload | Semaphores, bounded queues, `islice` feeding |
| Thread-unsafe shared state | Rare wrong results | Locks, queues, thread-local, immutable data |
| Deadlock | Everything idle forever | Lock ordering, timeouts, avoid nested locks; `faulthandler.dump_traceback_later(60)`; `py-spy dump` |
| Fork with threads/CUDA/locks | Hangs in children, CUDA errors | Use `spawn`/`forkserver`; fork early before threads |
| Pickle errors | `Can't pickle local object` | Top-level functions; data classes; avoid lambdas |
| Worker leaks | Memory growth in pools | `maxtasksperchild`, recycle, fix leaks, `tracemalloc` |
| Zombie/orphaned processes | Defunct processes, leftover workers | `wait()`, context managers, process groups, supervisors |
| Oversubscription | CPU throttling, slow runs | Match workers to cgroup limits; avoid nested parallelism (NumPy threads x process pool: set `OMP_NUM_THREADS=1`) |
| Thundering herd / retry storm | Target collapse | Jittered backoff, limits, circuit breakers |
| Lost exceptions in threads | Silent partial results | Use futures; `threading.excepthook` |
| `signal` in non-main thread | `ValueError: signal only works in main thread` | Install handlers in the main thread / `loop.add_signal_handler` |
| `asyncio.run()` inside a running loop | `RuntimeError` (Jupyter, frameworks) | `await` instead; `nest_asyncio` only for notebooks |

Tools: `faulthandler.enable()` and `faulthandler.dump_traceback_later(timeout, repeat=True)`, `kill -SIGUSR1` with `faulthandler.register`, `py-spy dump/top/record` (sampling, no code changes), `threading.enumerate()`, `sys._current_frames()`, `asyncio.all_tasks()`, `psutil.Process().num_threads()`, `ss -s`, `lsof -p`, `strace -f -p`, `perf`, `tracemalloc`, metrics for in-flight tasks, queue depth, and latency percentiles.

## 7. Lab (untested)

1. **GIL experiment**: time a CPU-bound function sequentially, with 4 threads, with 4 processes; time an I/O-bound function (sleep/HTTP to a local server) sequentially, with threads, with asyncio; plot or tabulate; check `sys.getswitchinterval()`; try a NumPy function and `hashlib` on large buffers with threads to see GIL release.
2. **Races and locks**: reproduce a lost update with `counter += 1`; fix with a lock; demonstrate a deadlock with two locks and fix by ordering; use `queue.Queue` producer/consumer with a bounded queue and sentinel shutdown.
3. **Executors**: build the health-check fan-out with `ThreadPoolExecutor` against a local mock server with random latency/failures; add per-call timeouts, aggregate errors; implement `bounded_map` and prove memory stays flat when mapping over 10 million generated items (compare with naive submit-all using `tracemalloc`/`/usr/bin/time -v`).
4. **Processes**: hash many files with `ProcessPoolExecutor`; compare `chunksize`, `spawn` vs `fork`, pickling failure with a lambda; use `SharedMemory` with NumPy to share a large array; show copy-on-write behaviour and `gc.freeze()`; kill a worker with `kill -9` and handle `BrokenProcessPool`.
5. **asyncio**: write the async fan-out with `aiohttp`/`httpx` and a semaphore, timeouts and error aggregation; scale to 5,000 concurrent requests against a local server; compare throughput and memory with threads; add `TaskGroup` and `except*`.
6. **Event-loop blocking**: insert `time.sleep(1)` and `requests.get` into a coroutine and observe stalls and debug-mode warnings; fix with `to_thread`; use `PYTHONASYNCIODEBUG=1`.
7. **Cancellation and shutdown**: implement the worker pool template; send SIGTERM mid-run; verify in-flight work finishes or cancels cleanly, no "Task exception was never retrieved" messages, and exit code is correct; test `CancelledError` swallowing bug.
8. **Backpressure**: slow consumer + fast producer with bounded `asyncio.Queue`; show memory with unbounded vs bounded queues.
9. **Retries**: implement jittered retries and circuit breaker; simulate a flapping dependency; show synchronized retry storm without jitter vs smooth with jitter.
10. **Subprocess concurrency**: run 200 `ping`/`ssh` commands with `asyncio.create_subprocess_exec` limited by a semaphore; compare with threads + `subprocess.run`; handle timeouts and zombie prevention.
11. **Diagnose hangs**: write a program with a deadlock and one with a blocked event loop; diagnose using `faulthandler`, `py-spy dump`, `asyncio.all_tasks()`.
12. **Containers**: run the process pool inside a container with `--cpus=2`; show `os.cpu_count()` vs `sched_getaffinity` and CPU throttling (`cpu.stat`).
13. **Clean up.**

Mark tested only after execution.

## 8. Common mistakes

- Using threads to speed up CPU-bound pure Python, or asyncio for blocking libraries without offloading.
- Unbounded concurrency (no semaphore, queue or pool limits), unbounded queues, and creating millions of futures.
- No timeouts; swallowing `CancelledError`; fire-and-forget tasks without references or error handling.
- Sharing mutable state across threads/processes instead of messages; assuming the GIL makes code thread-safe.
- Forking after threads/CUDA initialisation; forgetting `if __name__ == "__main__"` with spawn; passing unpicklable objects.
- Forgetting that exceptions in workers must be collected; aborting an entire fleet operation on the first failure (or hiding all failures).
- Retrying non-idempotent operations or retrying without jitter and caps.
- Sizing pools by `cpu_count()` in containers; nested parallelism (process pool x BLAS threads).
- Treating async as "faster"; for a few requests the overhead and complexity are not worth it.

## 9. Interview angles

- "Explain the GIL. When do threads help? When do you need processes?"
- "How would you query 10,000 servers concurrently and safely?"
- "Threads vs asyncio: trade-offs; how do they handle blocking calls?"
- "What's `asyncio.gather` vs `TaskGroup`? How does cancellation work?"
- "What is backpressure and how do you implement it in Python?"
- "A service's async handlers hang after a network blip. What do you check?" (timeouts, blocked loop, dropped tasks.)
- "Why does fork after CUDA initialisation fail? How do DataLoader workers avoid it?"
- "How do you shut down a multi-threaded/async worker gracefully on SIGTERM?"
- "How would you parallelise processing of a 5 TB dataset?" (shards, processes/Ray/Dask/Slurm arrays, IO, checkpointing.)

## 10. Checkpoint questions (40)

1. Concurrency vs parallelism? **A:** Overlapping progress vs simultaneous execution.
2. I/O-bound vs CPU-bound? **A:** Waiting-dominated vs compute-dominated.
3. What does the GIL protect? **A:** CPython's memory management/bytecode execution; one thread runs Python at a time.
4. When is the GIL released? **A:** During blocking I/O and many C extension calls.
5. Does the GIL make `x += 1` safe? **A:** No.
6. Free-threaded Python? **A:** Optional GIL-less builds (PEP 703).
7. Can you kill a thread? **A:** No; use cooperative cancellation.
8. What does `daemon=True` mean? **A:** Thread is killed at interpreter exit without cleanup.
9. What do `Lock` and `RLock` differ in? **A:** RLock is re-entrant by the same thread.
10. What is a deadlock? **A:** Tasks waiting on each other's resources forever.
11. How to avoid deadlock? **A:** Lock ordering, timeouts, fewer locks.
12. What does a bounded `Queue` provide? **A:** Backpressure.
13. `submit` vs `map`? **A:** Single future vs ordered iterator of results.
14. What does `as_completed` do? **A:** Yields futures as they finish.
15. Do executor timeouts stop the task? **A:** No; the work keeps running.
16. Why bound in-flight futures? **A:** Avoid memory blow-up.
17. When use `ProcessPoolExecutor`? **A:** CPU-bound pure Python.
18. Why `if __name__ == "__main__"`? **A:** Spawn re-imports the module.
19. What gets pickled in multiprocessing? **A:** Function arguments and results.
20. Fork vs spawn? **A:** Copy-on-write clone vs fresh interpreter.
21. Why avoid fork after CUDA? **A:** CUDA contexts aren't fork-safe.
22. What is `SharedMemory` for? **A:** Zero-copy sharing of buffers across processes.
23. What does `maxtasksperchild` do? **A:** Recycles workers to limit leaks.
24. `os.cpu_count()` in containers? **A:** Reports host CPUs, not the limit.
25. What is an event loop? **A:** Single-threaded scheduler for coroutines/IO.
26. Coroutine vs task? **A:** Awaitable object vs scheduled concurrently running wrapper.
27. What does `await` do? **A:** Suspends until the awaitable completes, yielding control.
28. Why keep task references? **A:** Loop holds weak refs; tasks may be collected.
29. `gather` vs `TaskGroup`? **A:** Collect results vs structured concurrency with cancellation on failure.
30. How to timeout a coroutine? **A:** `asyncio.timeout()` or `wait_for`.
31. What must you do on `CancelledError`? **A:** Clean up and re-raise.
32. How to run blocking code in asyncio? **A:** `asyncio.to_thread` / `run_in_executor`.
33. What blocks the loop? **A:** Sync I/O, `time.sleep`, CPU-heavy code.
34. How to debug asyncio? **A:** Debug mode, `all_tasks()`, py-spy.
35. What is backpressure in asyncio? **A:** Bounded queue making producers await.
36. What is full jitter? **A:** Random delay between 0 and the exponential cap.
37. Why per-host semaphores? **A:** Prevent overloading specific targets.
38. How to handle SIGTERM in asyncio? **A:** `loop.add_signal_handler` setting a stop event.
39. Tool to inspect a hung Python process? **A:** `py-spy dump` / `faulthandler`.
40. When shell `xargs -P` instead? **A:** Simple one-off parallel commands.

## 11. Sources and review notes

**Written in original words.** Principal sources:

- Luciano Ramalho, *Fluent Python*, 2nd ed.: chapter 19 (concurrency models in Python), chapter 20 (concurrent executors), chapter 21 (asynchronous programming).
- The author's `nvidia-devops` repository, volume 02 (Python systems and concurrency masterclass): the GIL and model selection, subprocess pitfalls (zombies, pipe deadlocks), `ThreadPoolExecutor` fan-out and backpressure, asyncio for BMC APIs, blocked-loop and thread-pool OOM scenarios, retries and jitter.
- Examples are the author's constructions.

**Flagged for verification before publishing:** the status of free-threaded Python and subinterpreter APIs by version, default start methods per Python version and platform, library behaviours (aiohttp/httpx/boto3 thread-safety), and every code listing; all labs are **untested**.
