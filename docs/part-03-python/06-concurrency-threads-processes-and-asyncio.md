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

Suppose you have to query 5,000 BMCs, health-check 800 nodes and tail logs from every pod. Other jobs upload 10 million objects, pre-process shards of a dataset, or serve many inference requests while a model runs. This is fan-out work: one job touches many machines or items at once. Doing it one item at a time is far too slow. Doing it concurrently without understanding the model, however, produces hangs, resource exhaustion, race conditions and runaway memory.

Python offers three concurrency models: threads, processes and asyncio. Each one has a different cost. The Global Interpreter Lock (GIL) decides which model fits which workload.

This chapter explains the models from first principles and shows you how to choose between them. It then covers the production patterns that matter most: bounded concurrency, backpressure, timeouts, cancellation, error aggregation, retries, graceful shutdown and diagnosing hangs. The ground it lays also prepares you for FastAPI services in chapter 3.7, exporters and agents in chapter 3.8, and data pipelines in chapter 3.10.

## Prerequisites and outcomes

Before you start, you should be comfortable with functions, generators and classes from chapters 3.1 to 3.4. You should also know the basics of subprocess and signal handling from chapter 3.5.

By the end of this chapter, you should be able to:

- Tell concurrency apart from parallelism, and I/O-bound work apart from CPU-bound work. Explain the GIL: what it protects, when it is released, and where free-threaded builds and subinterpreters stand.
- Use the `threading` module (Thread, Lock, RLock, Event, Condition, Semaphore, Queue), the `concurrent.futures` module (ThreadPoolExecutor, ProcessPoolExecutor) and the `multiprocessing` module (Process, Pool, Queue, shared memory), with correct synchronisation and cleanup.
- Write `asyncio` code with coroutines, tasks, `gather`, `TaskGroup`, `wait_for` and `timeout`, semaphores, queues, cancellation, async context managers and iterators, and async HTTP and subprocess calls. Run blocking code through `to_thread` or executors, so the event loop stays free.
- Choose a model for a workload, size its pools, and add backpressure with bounded queues.
- Recognise and avoid data races, deadlocks, livelocks, starvation, thundering herds, fork-safety problems and orphaned work.
- Aggregate results and errors from many concurrent operations. Implement retries with jitter, circuit breakers and rate limits, and shut down gracefully.
- Profile and debug concurrency problems with `faulthandler`, py-spy and asyncio debug mode.

## 1. Concepts

Imagine a script that must poll many endpoints while also crunching numbers on the same machine. Before you pick a model, you need to know whether the time goes to waiting or to computing. Those two situations call for different tools, and the terms below name the difference.

**Concurrency** means structuring a program so that several tasks make progress in overlapping time periods. Rob Pike defined it as "dealing with lots of things at once". **Parallelism** means running several computations at the same moment on several cores, or "doing lots of things at once". You can have concurrency without parallelism, because one core can interleave tasks.

**I/O-bound** work spends its time waiting for the network, disks, subprocesses or a sleep. Concurrency helps here even on one core, because the waits overlap. **CPU-bound** work spends its time computing. Only parallelism across cores, or faster code such as native libraries, speeds it up.

Latency and throughput measure different things. Amdahl's law states that speed-up is limited by the serial fraction of the work. Overheads such as thread creation, context switches and serialisation between processes can exceed the gains for small tasks.

Shared state is the enemy of concurrent code. The more tasks share mutable data, the more locks, races and bugs you get. Prefer **message passing** through queues, immutable data and per-task state.

```mermaid
flowchart TD
    Work{"What dominates runtime?"} -->|I/O-Bound: Waiting on network, BMCs, APIs, disk| Scale{"Concurrency scale & library support?"}
    Scale -->|"10 to 200 concurrent calls<br/>(blocking libs: requests, paramiko, boto3)"| TPE["ThreadPoolExecutor<br/>(GIL released during OS I/O)"]
    Scale -->|"1,000 to 10,000+ connections<br/>(async libs: httpx.AsyncClient, aiohttp, asyncpg)"| AsyncIO["asyncio Event Loop + Semaphore<br/>(offload disk/sync calls via asyncio.to_thread)"]
    Work -->|CPU-Bound: Parsing, hashing, math, compression| Kind{"Pure Python or Native C/Rust/CUDA?"}
    Kind -->|"Pure Python (is_prime, AST/JSON transforms)"| PPE["ProcessPoolExecutor / multiprocessing<br/>(1 process per physical core, separate GILs)"]
    Kind -->|"Native C/CUDA (NumPy, PyTorch, hashlib, zlib)"| Native["Vectorized / Native Calls<br/>(release GIL in C or use process-per-GPU torchrun)"]
```

### The Global Interpreter Lock

CPython, the reference implementation of Python, has a **GIL**. This mutex lets only one thread execute Python bytecode at a time within a process. The lock keeps memory management simple, because reference counting is not thread-safe without it, and it keeps C extensions simpler to write. Three consequences follow from it.

Threads do not speed up pure-Python CPU-bound code. They can even slow it down through contention and switching.

The GIL is released during blocking I/O, such as socket calls, file reads, `time.sleep` and subprocess waits. Many C extensions also release it during long computations, including NumPy, hashlib on large buffers, compression, regex in some cases, PyTorch ops, `zlib` and `bz2`. Threads therefore do speed up I/O-bound code and work that is heavy on native code.

Individual bytecode operations are atomic-ish, but compound operations are not thread-safe. `x += 1` and a check-then-act on a dict can still race. The GIL does not remove the need for locks.

Since Python 3.2, contributed by Antoine Pitrou, the interpreter switches threads on a time slice. That interval is `sys.getswitchinterval()`, which defaults to `0.005`s, or `5 ms`.

### A ten-minute experiment

Reading about the GIL is less convincing than watching it. The script below runs the same CPU-bound job three ways: one after another, on four threads, and on four processes. Each job chains 1,000,000 small SHA-256 hashes, which keeps the work inside the interpreter.

```python
import hashlib, time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def burn(seed: int) -> str:
    digest = str(seed).encode()
    for _ in range(1_000_000):
        digest = hashlib.sha256(digest).digest()
    return digest.hex()

def timed(label, run):
    t0 = time.perf_counter()
    run()
    print(f"{label:<14}{time.perf_counter() - t0:6.2f}s")

if __name__ == "__main__":
    jobs = list(range(8))
    timed("sequential", lambda: [burn(j) for j in jobs])
    with ThreadPoolExecutor(max_workers=4) as pool:
        timed("4 threads", lambda: list(pool.map(burn, jobs)))
    with ProcessPoolExecutor(max_workers=4) as pool:
        timed("4 processes", lambda: list(pool.map(burn, jobs)))
```

On a machine with at least four free cores, expect the thread run to take about as long as the sequential run, or a little longer. Every thread must hold the GIL to run Python code, so they take turns. The process run should be clearly faster, because each worker process has its own interpreter and its own GIL. Your timings depend on your hardware, so record your own. Then change the job to an I/O wait, such as `time.sleep(1)`, and rerun: now the threads win, because the GIL is released while a thread sleeps.

Two more facts explain the rest of this chapter. A thread that computes for a long time is paused every few milliseconds so that others can run, which is why a threaded program stays responsive. An asyncio task is never paused that way. It runs until it reaches an `await`, so one CPU-bound call freezes every other task on the loop.

Production web stacks take a different route. Instead of one multi-threaded process, they scale across CPU cores. An application server such as gunicorn, uWSGI or uvicorn preforks one worker process per core, behind a reverse proxy such as NGINX or Envoy. Shared state moves to external services: caches such as Redis, databases such as PostgreSQL, and task queues such as Celery or RabbitMQ.

Free-threaded CPython, defined in PEP 703, is an optional build that runs without the GIL. Builds from 3.13 onward offer it in experimental form as `python3.13t`, and later releases support it. Extension compatibility and single-thread overhead are still evolving, so check each dependency. Subinterpreters, defined in PEP 684 and PEP 734, give each interpreter its own GIL, and `concurrent.interpreters` arrives in 3.14. Treat both as emerging. The models in the rest of this chapter remain the practical toolkit.

Other options exist too. Processes have separate GILs. Native extensions such as Cython, Numba and Rust through PyO3 move the work out of Python. Vectorised libraries such as NumPy, pandas and PyTorch spend their time outside the interpreter.

### Choosing a model

The table is a lookup. Find your workload in the first column and read across to the model that fits it. Notice that blocking libraries point you toward threads, while async libraries point you toward asyncio.

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

Size your pools with a few simple rules. For threads that do I/O, match the concurrency the remote system can tolerate, not the largest number you can start. For processes that do CPU work, use the number of cores, which you can read with `os.cpu_count()` or `len(os.sched_getaffinity(0))`, or the cgroup CPU limit when you run in a container. For asyncio, cap concurrency with a semaphore at what the target and your sockets can sustain.

Always apply **bounded concurrency**. Unbounded fan-out overwhelms the targets, for example as a thundering herd on a BMC network or an API. It also exhausts your own file descriptors and memory. Set the limit before you write the loop, because the limit is what keeps the fan-out safe.

## 2. Threads

### Basics

Start with the simplest case: five threads that each wait and then report. The code joins them with a timeout, so a stuck thread shows up instead of freezing your script.

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

Daemon threads are killed abruptly when the interpreter exits, with no cleanup. Use them only for background chores you can afford to drop. Non-daemon threads keep the process alive until they finish.

An exception raised inside a thread does not reach the main thread. The thread prints a traceback and ends. Capture the error with executors and futures, or set `threading.excepthook`.

No code can kill a thread from outside. Design cooperative cancellation instead: give the workers a `threading.Event` to check, and bound every blocking call with a socket timeout or `queue.get(timeout=)`. Use `threading.local()` for state that belongs to one thread, and `contextvars` for context that follows tasks and threads.

### Synchronisation primitives

Threads share memory, so you need tools to coordinate them. The table lists each primitive and what it is for. Notice that `Lock` guards data, while `Event` and `Condition` signal between threads.

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

Here is why the lock matters. Without it, two threads can interleave the load, add and store steps of `counter += 1` and lose an update.

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

The `with lock:` block makes those steps one protected unit, so no update disappears.

Shared state brings several bugs. A **data race** loses updates or breaks an invariant. A **deadlock** happens when two threads each hold a lock the other one needs. You can avoid it with a global lock order, by acquiring locks with timeouts, or by holding at most one lock. Livelock, starvation and priority inversion are other traps. Keep critical sections tiny and free of I/O. Never call unknown callbacks while you hold a lock. Prefer queues and immutable messages over shared mutable data, and test with stress loops.

### Producer/consumer with a bounded queue

A bounded queue stops a fast producer from flooding memory. When the queue is full, `put()` waits until the consumers catch up. The sentinel object tells each consumer that no work is left.

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

`task_done()` marks each item as finished, so `join()` can tell when all the work is complete.

### `concurrent.futures`

`concurrent.futures` is the high-level API for pools. You submit callables and get `Future` objects back.

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

`as_completed` yields each future as soon as it finishes, so one slow host does not hold up the report. The `try` block around `fut.result()` re-raises the worker's exception at that point, where you can record it.

`pool.map(fn, iterable, timeout=..)` returns a generator. It yields results in the exact order of the input `iterable`, and it raises the first exception when that item is reached. The order matters. Suppose you check 20 hosts and the second one is slow. With `pool.map`, the results for hosts 3 to 20 sit finished but unreported until host 2 returns, so a progress display appears to freeze even though the workers are busy.

When you want each result as soon as its task finishes, combine `executor.submit` with `futures.as_completed`. Keep a dictionary that maps every submitted `Future` back to its input, as `futs` does in the example above. The loop then runs `for fut in as_completed(futs):`, can report live progress, and ties each exception to the host that caused it. The function `run_threadpool_to_do_map()` in `code/part03/python_concurrency_models.py` models this pattern.

A `Future` gives you `Future.result(timeout)`, `.exception()`, `.cancel()` (which works only if the task has not started), `.add_done_callback()` and `.done()`. Leaving the `with` block waits for all pending work, through `shutdown(wait=True)`. If an exception occurs, `shutdown(wait=False, cancel_futures=True)`, available from 3.9, drops the queued tasks. Executors do not interrupt running tasks when a timeout expires, so set timeouts on the I/O inside each task.

### Backpressure with executors (avoiding the "10 million futures" OOM)

A loop that calls `pool.submit(...)` for every item in a huge iterable creates all the futures at once and holds them. Memory grows before any work has started. The helper below feeds the pool in a bounded way instead.

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

The helper keeps at most `max_inflight` futures alive. Each time some of them finish, it yields their results and submits the same number of new items. Memory therefore stays at `O(max_inflight)`, however large the input is. This is a classic production fix for S3 listing and copy jobs and for fleet-wide commands.

### Thread safety of common objects

`queue.Queue`, `logging`, single `list.append` and `pop` calls, and single `dict` operations are safe. Compound operations are not. Never assume a client object is safe to share between threads. Among common clients, only the low-level `boto3` client is documented as thread-safe, while `boto3` sessions and resources are not. A `requests.Session` is mostly safe for simple use, but its documentation makes no strong guarantee. A single paramiko `SSHClient` is not designed for concurrent use from several threads, so open one connection per worker. Database drivers differ: the DB-API `threadsafety` attribute of the driver module tells you whether threads may share the module, a connection or neither. By default, `sqlite3` refuses to use a connection from another thread. When in doubt, create one client per thread with `threading.local()`.

## 3. Processes

Processes get around the GIL, because each one runs its own interpreter. The example below hashes large files in a pool of worker processes, so the hashing can use several cores at once.

### `multiprocessing` and `ProcessPoolExecutor`

```python
from concurrent.futures import ProcessPoolExecutor
import os, hashlib

def sha(path):                       # must be a top-level function: arguments and results are pickled
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return path, h.hexdigest()

if __name__ == "__main__":           # REQUIRED with spawn and forkserver (the default on macOS and Windows, and on Linux from 3.14): guards re-import
    files = [...]
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
        for path, digest in pool.map(sha, files, chunksize=16):          # chunksize batches IPC for many small tasks
            print(digest, path)
```

Each process starts in one of three ways. `fork` copies the parent quickly, using copy-on-write, but it is unsafe with threads, with locks held at fork time, with CUDA contexts and with open sockets. It was the default on Linux up to Python 3.13. `spawn` starts a fresh interpreter that imports your module. It is safe but slower, and it needs picklable arguments and the `if __name__ == "__main__"` guard. `forkserver` has a clean server process fork the workers, and it became the default on Linux, and other POSIX systems except macOS, in Python 3.14. macOS and Windows default to `spawn`. Select a method with `multiprocessing.set_start_method("spawn")` or `mp_context=multiprocessing.get_context("forkserver")`.

**Never use `fork` after initialising CUDA.** That is why PyTorch DataLoader workers and distributed launchers use `spawn` or `forkserver`. Avoid forking a process that has running threads or gRPC or OpenMP state, too.

Arguments and return values cross process boundaries through pickle. Lambdas, nested functions, open files, sockets and locks cannot be pickled, so use top-level functions and plain data. Large objects get copied, which is slow. Pass file paths or indices instead, or use shared memory.

Several tools share data between processes: `multiprocessing.Queue/Pipe/Manager`, `Value` and `Array` (ctypes, with locks), and `multiprocessing.shared_memory.SharedMemory`. `SharedMemory` gives you zero-copy buffers, and it is the basis for NumPy arrays shared across processes. Memory-mapped files work too, through `numpy.memmap`. Under `fork`, read-only data is shared copy-on-write. Reference-count writes can trigger page copies, and `gc.freeze()` helps.

`multiprocessing.Pool(processes)` offers `map`, `imap_unordered`, `apply_async` and `starmap`. Set `maxtasksperchild` to recycle leaky workers. Use `initializer` to set up per-worker state, such as opening a model or a database connection.

Each process takes tens of milliseconds to start, plus the time for its imports. Serialising data between processes adds cost, and memory gets duplicated. Use chunking, long-lived workers and coarse-grained tasks to keep those costs small.

An exception in a worker re-raises in the parent, with its traceback text attached. If the OOM killer stops a worker, you get `BrokenProcessPool`, which you must handle and recover from. Set resource limits as well.

Under `fork`, children inherit signal handlers. Handle `SIGTERM` in the parent and call `pool.terminate()` to stop the children. If the parent is killed with `SIGKILL`, the workers can be orphaned. To clean them up, use `prctl(PR_SET_PDEATHSIG)` or a supervisor such as systemd or Kubernetes. Use `daemon=True` with care.

`os.cpu_count()` reports the host's CPUs, not the container's CPU limit. Use `len(os.sched_getaffinity(0))`, or read the cgroup `cpu.max` file. If you oversubscribe a CPU-limited container, the kernel throttles it, and the throttling shows up in `cpu.stat`.

Size your pools to the cores your container really gets, and keep the tasks coarse so the overhead stays small.

### GPUs and data loading

PyTorch's `DataLoader(num_workers=N)` uses worker processes to decode and augment data. Tune `num_workers`, `prefetch_factor`, `pin_memory` and `persistent_workers`. Avoid forking after CUDA is initialised, and watch for memory duplication. Training launchers such as `torchrun`, accelerate, DeepSpeed, `mpirun` and Slurm `srun` give each GPU its own process. Concurrency here means one process per GPU, with NCCL handling communication, as Part 14 covers. Threads inside a rank are for I/O, such as prefetching, not for compute. Keep one process per GPU, and let threads handle only the I/O.

## 4. asyncio

### Why asyncio

Threads are heavy. Each one has its own stack and is scheduled by the kernel, so you can run only thousands of them. asyncio takes another route. It runs many tasks cooperatively on one thread, using an event loop and non-blocking I/O through epoll or kqueue. A task runs until it hits an `await` on something that is not ready. Then it yields control, so tens of thousands of concurrent connections cost very little. The price is that all code on the loop must be non-blocking, libraries must be async-aware, and any CPU-bound or blocking call stalls every task.

### Core concepts

The example below fetches many health endpoints through a semaphore, so no more than 100 requests run at once.

```python
import asyncio
import aiohttp

async def fetch(session, host):                   # coroutine function: calling it returns a coroutine object (does not run yet)
    timeout = aiohttp.ClientTimeout(total=5)       # aiohttp wants a ClientTimeout object, not a bare number
    async with session.get(f"https://{host}/healthz", timeout=timeout) as r:
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

A coroutine is an `async def` function. Calling it returns a coroutine object without running it. `await` suspends the caller until the awaited coroutine, future or task completes. You can use `await` only inside an `async def` function.

`asyncio.create_task(coro)` schedules a coroutine to run concurrently. Keep a reference to the task. The loop holds only weak references, so a task you drop can be garbage collected mid-flight. Tasks can be awaited, cancelled and inspected.

The event loop is a single-threaded scheduler. `asyncio.run()` is the entry point. Avoid `get_event_loop()` outside a running context.

`gather(*aws, return_exceptions=True)` runs awaitables concurrently and collects their results. With `return_exceptions=False`, the first exception propagates, but the others keep running. `TaskGroup`, added in 3.11, gives you structured concurrency. Tasks started in the group are awaited on exit. If one fails, the others are cancelled and an `ExceptionGroup` is raised.

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

In `poll_all`, the `except*` clause handles the `TimeoutError` exceptions that the group collects. Then the function returns `results`.

Use `await asyncio.wait_for(coro, timeout)` or the `async with asyncio.timeout(10):` block, available from 3.11. Every network await needs a timeout. Without one, you get a silent hang, where a half-open connection waits forever.

`task.cancel()` raises `asyncio.CancelledError` at the task's current `await`. Clean up in a `finally` block and re-raise `CancelledError`. Never swallow it. Use `asyncio.shield()` to protect critical sections. Timeouts and `TaskGroup` both rely on cancellation.

`asyncio.Lock`, `Semaphore`, `Event`, `Condition` and `Queue` are the async versions of the thread primitives. A bounded `Queue`, created with `maxsize`, gives you backpressure, because `await q.put()` waits while the queue is full. These primitives are not thread-safe across threads. An `asyncio.Semaphore(100)` throttles active HTTP requests, as the earlier example does. Wrap each request in `async with semaphore:`, and use `asyncio.as_completed` to handle results as they arrive.

An asynchronous iterable implements `__aiter__`, which returns an asynchronous iterator. That iterator defines `async def __anext__`, which raises `StopAsyncIteration` when it runs out. `async with` uses `__aenter__` and `__aexit__`, or the `contextlib.asynccontextmanager` decorator.

An asynchronous generator combines `async def` with `yield`. A useful case is a probe that checks many hosts and yields each result as it completes: it starts one coroutine per host, loops over `asyncio.as_completed`, awaits each finished one, and yields its result.

PEP 530 lets you use `async for` and `await` directly inside comprehensions and generator expressions. Examples include `[x ** 2 async for x in AsyncRange(1, 5)]`, `{name: found async for name, found in multi_probe(names)}`, and `{name for name in names if (await probe(name)).found}`. Note that `async for` awaits each item in turn, as the iterator yields it. To run a batch of coroutines concurrently, use `await asyncio.gather(*coros)` or `asyncio.TaskGroup`.

Standard Python has no portable non-blocking file writes, so wrap a blocking save in `await asyncio.to_thread(save, data, path)` and the event loop never stalls on disk. Async database drivers and stream writers split their work into explicit `await` stages, for example `writer.write(data); await writer.drain()`.

`asyncio.create_subprocess_exec(*cmd, stdout=PIPE)`, followed by `await proc.communicate()`, runs a command without blocking. Because `communicate` reads both streams, it avoids pipe deadlocks.

Use `await asyncio.to_thread(blocking_fn, args)`, available from 3.9, or `loop.run_in_executor(executor, fn, *args)`, to run blocking or CPU-heavy code off the loop. For CPU-bound work, pass a `ProcessPoolExecutor` to `run_in_executor`.

Common async libraries include aiohttp, httpx, asyncssh, aiofiles (which uses threads under the hood), asyncpg, aioredis/redis.asyncio, aiokafka, `kubernetes_asyncio`, aioboto3, aiobotocore and grpc.aio. Sync libraries such as requests, paramiko and boto3 block the loop when they run inside coroutines, so wrap them with `to_thread`.

Run `asyncio.run(main(), debug=True)`, or set `PYTHONASYNCIODEBUG=1`, to switch on debug mode. It logs callbacks that run longer than 100 ms, coroutines that were never awaited, and tasks destroyed while still pending. Use `loop.slow_callback_duration` for the slow-callback threshold. Use `asyncio.all_tasks()` and `task.print_stack()` to see where tasks are stuck. When the loop itself is blocked, `py-spy dump --pid` shows the stacks.

`uvloop` is a faster drop-in event loop for Linux and macOS, and it improves throughput for servers. Behaviour differs between platforms, with selector and proactor loops as one example. Production Linux is the norm.

### A worker-pool template

This template ties the earlier pieces together: a bounded queue, a fixed set of workers, per-item timeouts, and clean shutdown on signals.

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

The template has bounded memory, bounded concurrency, per-item timeouts and error isolation, and clean cancellation on signals. Tune `concurrency` and `queue_size` to what your targets can take, and you have a fleet loop you can trust.

## 5. Patterns for infrastructure fan-out

### Retries, backoff and jitter

Retry only idempotent operations and transient errors, such as timeouts, connection resets, 429 or 503 responses. Use exponential backoff with **full jitter**, so that retries from many clients do not synchronise into a storm. Cap the total time, honour `Retry-After`, and log each attempt.

```python
import asyncio, random

async def retry(fn, *, attempts=5, base=0.5, cap=20.0, retry_on=(asyncio.TimeoutError, ConnectionError)):
    for i in range(attempts):
        try:
            return await fn()
        except retry_on as exc:
            if i == attempts - 1: raise
            delay = random.uniform(0, min(cap, base * 2 ** i))            # full jitter
            await asyncio.sleep(delay)
```

On each failed attempt, the `retry` helper waits a random delay between zero and the smaller of `cap` and `base * 2 ** i`. On the last attempt it re-raises the error instead.

Libraries such as `tenacity` and `backoff` implement this for you. HTTP clients also have retry adapters, for example `urllib3.util.Retry` with `requests.adapters.HTTPAdapter`.

### Rate limiting and circuit breaking

Protect the targets, and protect yourself. A token bucket, from `aiolimiter` or from an asyncio semaphore plus a sleep, limits the rate. Per-host concurrency limits, with one semaphore per host, rack or BMC network, keep any single target from being overloaded. A circuit breaker stops calling a failing dependency for a cool-down period. Handle `Retry-After` too, and consider adaptive concurrency, such as AIMD, the approach TCP uses. For BMC and Redfish fleets, limit concurrency per rack, so the management switches are not overwhelmed.

### Aggregating results

Return a `Result(host, ok, value|error, duration)` for each item. Summarise at the end with the success and failure counts, the slowest items and the error classes. Exit non-zero if a critical failure occurred, and keep the raw errors for diagnosis. Do not let one exception abort everything unless you mean it to. Use `return_exceptions=True`, or catch errors inside the worker.

### Streaming and pagination

Combine async generators with queues to build pipelines. A producer loops with `async for page in client.list_pages(): await q.put(page)`. Consumers process the pages in parallel, under bounded concurrency. Memory stays flat, because the queue's bound limits how many pages wait at once.

### Scheduling and periodic tasks

A simple periodic loop looks like `while not stop.is_set(): await run_once(); await asyncio.wait_for(stop.wait(), timeout=interval)`. The wait is interruptible, so a stop signal ends the loop without waiting out the full interval. Use `time.monotonic()` for intervals that do not drift. For cron-style schedules, prefer systemd timers, Kubernetes CronJobs or APScheduler. Compute the next deadline rather than sleeping a fixed amount, so the drift does not build up.

### Combining models

The three models can work together.

Mix asyncio with processes using `await loop.run_in_executor(process_pool, cpu_fn, data)`. Mix threads with asyncio by submitting coroutines from a thread with `asyncio.run_coroutine_threadsafe(coro, loop)`, and by touching the loop with `loop.call_soon_threadsafe`.

Multiprocess web servers, such as gunicorn or uvicorn workers, give each process its own event loop, so they scale across cores. Share state through external stores such as Redis, not through memory.

FastAPI `BackgroundTasks` suit short fire-and-forget work. For durable work, use real queues, which chapter 3.7 covers.

### Distributed concurrency

When one machine is not enough, you move to Slurm job arrays and `srun`, Kubernetes Jobs with `completions`, `parallelism` and indexed jobs, Ray remote functions and actors, Dask, or Celery and RQ workers. Idempotency, checkpointing and at-least-once semantics matter more than the in-process model. Design for those three first, before you choose the framework.

## 6. Pitfalls and diagnosis

Most concurrency bugs show up as a symptom first. Start from the symptom you see, then read across the row to its likely cause and remedy. If your service hangs, for instance, begin with the rows about timeouts and blocked loops.

| Problem | Symptom | Cause / remedy |
|---|---|---|
| Blocking the event loop | Tasks stall, timeouts everywhere, loop "slow callback" warnings | Sync I/O (`requests`, `time.sleep`, `subprocess.run`, heavy CPU) in a coroutine: use async APIs or `to_thread` |
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

Most of these rows come down to two habits: put a timeout on every wait, and bound every queue and pool.

Several tools help you find the cause. Use `faulthandler.enable()` and `faulthandler.dump_traceback_later(timeout, repeat=True)`, or `kill -SIGUSR1` with `faulthandler.register`. `py-spy dump`, `py-spy top` and `py-spy record` sample a process without any code changes. Then there are `threading.enumerate()`, `sys._current_frames()`, `asyncio.all_tasks()`, `psutil.Process().num_threads()`, `ss -s`, `lsof -p`, `strace -f -p`, `perf` and `tracemalloc`. Track metrics for in-flight tasks, queue depth and latency percentiles as well.

## 7. Lab

Start by running the self-checking lab on your own machine, so you can see each model pass its checks. It verifies a CPU-bound primality check, a threaded task that keeps running next to CPU work, and an asyncio task that is cancelled with `Task.cancel` and `CancelledError`. It also checks the `as_completed` pattern, the `bounded_map` backpressure helper, `asyncio.Semaphore` fan-out, `asyncio.to_thread` offloading, async generators and async comprehensions.

```bash
python3 code/part03/python_concurrency_models_lab.py
```

Then, on any machine with Python 3.11 or later, work through these exercises yourself. The interactive steps were not run on live hardware, so confirm each result on your own machine.

1. Run a GIL experiment. Time a CPU-bound function sequentially, with 4 threads, and with 4 processes. Time an I/O-bound function, a sleep or an HTTP call to a local server, sequentially, with threads, and with asyncio. Plot or tabulate the results. Check `sys.getswitchinterval()`, then try a NumPy function and `hashlib` on large buffers with threads, to see the GIL being released.
2. Reproduce a lost update with `counter += 1`, then fix it with a lock. Demonstrate a deadlock with two locks, and fix it by ordering them. Finally, build a producer and consumer with a bounded `queue.Queue`, shut down with a sentinel.
3. Build the health-check fan-out with `ThreadPoolExecutor` against a local mock server that has random latency and failures. Add per-call timeouts and aggregate the errors. Implement `bounded_map`, then prove that memory stays flat when it maps over 10 million generated items. Compare that with a naive submit-all approach, using `tracemalloc` or `/usr/bin/time -v`.
4. Hash many files with `ProcessPoolExecutor`. Compare `chunksize`, and compare `spawn` with `fork`. Trigger a pickling failure with a lambda. Use `SharedMemory` with NumPy to share a large array. Show copy-on-write behaviour and `gc.freeze()`. Kill a worker with `kill -9`, and handle `BrokenProcessPool`.
5. Write the async fan-out with `aiohttp` or `httpx` and a semaphore, with timeouts and error aggregation. Scale it to 5,000 concurrent requests against a local server, and compare throughput and memory with threads. Add `TaskGroup` and `except*`.
6. Insert `time.sleep(1)` and `requests.get` into a coroutine, and observe the stalls and the debug-mode warnings. Fix them with `to_thread`, and run again with `PYTHONASYNCIODEBUG=1`.
7. Implement the worker-pool template. Send SIGTERM in the middle of a run. Verify that in-flight work either finishes or cancels cleanly, that no "Task exception was never retrieved" messages appear, and that the exit code is correct. Test the `CancelledError` swallowing bug too.
8. Run a slow consumer with a fast producer, connected by a bounded `asyncio.Queue`. Show the memory use with an unbounded queue and with a bounded one.
9. Implement jittered retries and a circuit breaker. Simulate a flapping dependency, and show a synchronised retry storm without jitter, then smooth retries with jitter.
10. Run 200 `ping` or `ssh` commands with `asyncio.create_subprocess_exec`, limited by a semaphore. Compare with threads and `subprocess.run`. Handle timeouts, and prevent zombie processes.
11. Write one program with a deadlock and one with a blocked event loop. Diagnose both with `faulthandler`, `py-spy dump` and `asyncio.all_tasks()`.
12. Run the process pool inside a container with `--cpus=2`. Show `os.cpu_count()` and `sched_getaffinity` side by side, and show the CPU throttling in `cpu.stat`.
13. Clean up.

## 8. Common mistakes

Many mistakes come from picking the wrong tool. You might choose threads for CPU-bound pure Python, and asyncio with blocking libraries that never get offloaded is another. Treating async as faster by default is a third. For a handful of requests, the overhead is not worth it.

Unbounded work is a trap too. Concurrency with no semaphore, queue or pool limit, unbounded queues and millions of futures all exhaust memory and sockets.

Error handling fails quietly. Missing timeouts, swallowed `CancelledError`, and fire-and-forget tasks without references cause silent failures. Forgetting to collect worker exceptions, or aborting a fleet operation on the first failure, hides the failures that matter.

Shared state is risky. Sharing mutable state across threads or processes, instead of passing messages, invites races. So does assuming the GIL makes code thread-safe.

Process setup breaks quietly too. Forking after threads or CUDA initialisation, forgetting `if __name__ == "__main__"` with spawn, and passing unpicklable objects all cause failures.

Retries need care. Retrying non-idempotent operations, or retrying without jitter and caps, can make an outage worse.

Pool sizing is easy to get wrong. Sizing pools by `cpu_count()` inside containers, or nesting a process pool over BLAS threads, oversubscribes the cores. Check that every pool and queue has a limit, and every await has a timeout, before you ship.

## 9. Interview angles

Each question below tests a different part of the chapter. Answer it aloud before you check your reasoning against the sections above.

- "Explain the GIL. When do threads help? When do you need processes?"
- "How would you query 10,000 servers concurrently and safely?"
- "Threads vs asyncio: trade-offs; how do they handle blocking calls?"
- "What's `asyncio.gather` vs `TaskGroup`? How does cancellation work?"
- "What is backpressure and how do you implement it in Python?"
- "A service's async handlers hang after a network blip. What do you check? Start with timeouts, a blocked loop and dropped tasks."
- "Why does fork after CUDA initialisation fail? How do DataLoader workers avoid it?"
- "How do you shut down a multi-threaded/async worker gracefully on SIGTERM?"
- "How would you parallelise processing of a 5 TB dataset? Think about shards, processes or Ray, Dask and Slurm arrays, I/O and checkpointing."

## Exercises

Each exercise is one fan-out job you could be asked to build. Run them against local mock servers or loopback addresses.

1. A script must poll the Redfish endpoint of 5,000 BMCs, and a sequential loop takes hours. Build the poll with `asyncio`, a semaphore of 100 and an `aiohttp.ClientTimeout`. Return one result record per BMC, so that a dead BMC never aborts the run.
2. A health check of 800 nodes uses the blocking `requests` library. Rebuild it with `ThreadPoolExecutor` and `as_completed`, with a timeout on every call. Print the count of failures and the three slowest hosts.
3. A job lists 10 million S3 keys and submits one future per key, and it runs out of memory. Use `bounded_map()` from this chapter to keep memory flat, and show the difference with `tracemalloc`.
4. A pre-processing step hashes thousands of dataset shards in pure Python. Time it sequentially, on threads and on processes, using the experiment in this chapter as a base. Then run it in a container limited with `--cpus=2` and compare `os.cpu_count()` with `len(os.sched_getaffinity(0))`.
5. An async collector calls `time.sleep` and a blocking `requests.get` inside coroutines, and every host stalls. Run it with `PYTHONASYNCIODEBUG=1` to see the slow-callback warnings. Fix it with `asyncio.to_thread`, then send SIGTERM during a run of the worker-pool template and confirm that the pool drains cleanly.
6. A fleet of clients retries a failing API at the same moments, and the API never recovers. Implement the jittered `retry()` helper with a circuit breaker. Simulate a flapping dependency, and compare the request pattern with and without jitter.

## Checkpoint questions (20)

<details>
<summary>1. Distinguish Concurrency from Parallelism and I/O-bound from CPU-bound workloads.</summary>

- **Concurrency** means a program juggles several tasks so they overlap in time. For example, one core can interleave them, and that still counts. It is "dealing with lots of things at once". **Parallelism** means running several computations at the same moment on multiple physical CPU cores or GPUs. It is "doing lots of things at once".
- **I/O-bound** work mostly waits on network sockets, disks or subprocesses, and concurrency with `asyncio` or threads overlaps those waits. **CPU-bound** work spends its time executing instructions, so it needs multi-process parallelism, or native C, Rust or CUDA code, to go faster.
</details>

<details>
<summary>2. What is the CPython GIL, when is it released, and why doesn't it make `counter += 1` thread-safe?</summary>

The **Global Interpreter Lock (`GIL`)** is a mutex in CPython. It lets only one thread per process run Python bytecode at a time, and it protects CPython's reference counting and C extension state.
- **When released:** The GIL is released during blocking OS I/O, such as `socket` calls, file reads and writes, `time.sleep` and `subprocess`. Many C extensions release it during heavy native work, including NumPy, PyTorch, `hashlib`, `zlib` and `bz2`.
- **Why `counter += 1` still races:** CPython switches threads every `5 ms` (`sys.getswitchinterval()`). The statement `counter += 1` compiles into several bytecode steps, `LOAD_GLOBAL`, `BINARY_OP` and `STORE_GLOBAL`, so a switch between the load and the store loses an update. Only a `with threading.Lock():` block prevents that. Python 3.13 and later offer experimental free-threaded builds under PEP 703, and subinterpreters use PEP 684.
</details>

<details>
<summary>3. A status spinner runs in a thread, a process or an asyncio task while the main work switches from a 3-second sleep to a long CPU-bound computation. What happens to each spinner?</summary>

- **Spinner in a thread:** Keeps spinning. The computation is pure-Python CPU work, but CPython pauses it every 5 ms (`sys.getswitchinterval()`). That gives the spinner thread time to wake, print one character and release the GIL again.
- **Spinner in a process:** Keeps spinning in true parallelism, because the child process has its own interpreter and its own GIL, on another core.
- **Spinner in an asyncio task:** Freezes completely. The event loop is single-threaded and cooperative, with no time slicing. The computation has no `await`, so it holds the thread until it finishes, starving the spinner the whole time.
</details>

<details>
<summary>4. How do you stop a Python `Thread` versus an `asyncio.Task`, and what does `daemon=True` mean?</summary>

- **Stopping a `Thread`:** You cannot kill or interrupt a Python thread from outside. Use cooperative cancellation instead. Pass a **`threading.Event`** (`done`), and have the worker check it in its loop, as in `while not done.wait(timeout):`. Keep all blocking I/O time-bounded, so the thread can exit and be joined with `t.join(timeout=10)`.
- **Stopping an `asyncio.Task`:** `task.cancel()` schedules an **`asyncio.CancelledError`** at the coroutine's suspended `await`. The coroutine runs its `finally:` cleanup, and it must re-raise `CancelledError`.
- **`daemon=True`:** A daemon thread stops abruptly when the main thread exits. It skips `finally:` blocks and does not flush files. Non-daemon threads keep the process alive until they finish.
</details>

<details>
<summary>5. Compare `Lock`, `RLock`, `Event`, `Condition`, `Semaphore`, and `queue.Queue(maxsize=N)`.</summary>

- **`Lock`** is a basic mutex. Acquiring it twice in the same thread deadlocks.
- **`RLock`** is re-entrant. The same thread can acquire it several times, but it must release it the same number of times.
- **`Event`** is a thread-safe boolean flag, with `set()`, `clear()` and `wait(timeout)`, used for start and shutdown signals.
- **`Condition`** pairs a lock with a wait set. It offers `wait_for(predicate)`, `notify()` and `notify_all()` for state changes.
- **`Semaphore(N)` and `BoundedSemaphore(N)`** cap concurrent access at `N` threads.
- **`queue.Queue(maxsize=N)`** is a thread-safe FIFO queue. `put()` blocks once `maxsize` is reached, which gives fast producers automatic **backpressure**. `task_done()` and `join()` track completion, and a `SENTINEL = object()` poison pill tells workers to exit.
</details>

<details>
<summary>6. Contrast `executor.map()` with `executor.submit()` + `as_completed(to_do_map)` in `concurrent.futures`.</summary>

- **`executor.map(fn, iterable)`** yields results strictly in the order of `iterable`. If the second of 20 tasks takes 11 seconds while the other 18 take microseconds, `executor.map` waits for item 2 before it yields items 3 to 20. It also raises the first exception it meets during iteration.
- **`executor.submit(fn, x)` + `as_completed(to_do_map)`** yields futures in completion order, through `for fut in as_completed(to_do_map):`. The dictionary `to_do_map = {executor.submit(fn, h): h for h in hosts}` maps each future back to its input. That allows immediate progress reporting and per-host error isolation, through `try: res = fut.result() except Exception as exc: errors[to_do_map[fut]] = exc`.
</details>

<details>
<summary>7. Why does `[pool.submit(fn, x) for x in ten_million_items]` cause an Out-Of-Memory crash, and how does `bounded_map` fix it?</summary>

Submitting every item up front creates 10 million `Future` objects, their closure arguments and their internal work-queue entries in RAM, before the workers can drain them. That can consume gigabytes. `bounded_map` seeds the pool with at most `max_inflight` futures, using `islice(it, max_inflight)`. It then waits for at least one to finish, with `done, inflight = wait(inflight, return_when=FIRST_COMPLETED)`, yields those results, and submits only `len(done)` replacements from `islice(it, len(done))`. Memory stays at **`O(max_inflight)`**.
</details>

<details>
<summary>8. Compare the three `multiprocessing` start methods (`fork`, `spawn`, `forkserver`), and explain why you must never `fork` after initializing CUDA or threads.</summary>

- **`fork`** clones the parent with copy-on-write. It is fast, but only the calling thread is duplicated. If another thread held a mutex, such as a Python lock, glibc `malloc`, gRPC, OpenMP or the **CUDA driver runtime**, that lock stays locked forever in the child. The result is a deadlock or a `CUDA_ERROR_NOT_INITIALIZED` crash.
- **`spawn`** starts a fresh interpreter and re-imports the main module. It is required on macOS and Windows, and it is the default only on macOS and Windows, since Python 3.14 made `forkserver` the Linux default. It needs **`if __name__ == "__main__":`** and picklable top-level functions and arguments.
- **`forkserver`** forks workers from a clean, single-threaded server process. It is the default on Linux from Python 3.14. That server starts before CUDA or threads are initialised.
</details>

<details>
<summary>9. How do you share large numeric arrays across worker processes without pickling overhead or copy-on-write page faults?</summary>

1. Use **`multiprocessing.shared_memory.SharedMemory`**, or `numpy.memmap`. Both give you an OS shared-memory buffer that processes attach to by name, with no serialisation or copying.
2. Call **`gc.freeze()` before forking** when the data is read-only, under `forkserver` or `fork`. It moves all currently allocated Python objects into the permanent GC generation. Reference-count and GC header writes during reads then do not dirty copy-on-write pages.
3. Pass **`chunksize=16`**, or higher, to `ProcessPoolExecutor.map` to batch IPC transfers across many small items. Use `maxtasksperchild` on `multiprocessing.Pool` to recycle leaky workers.
</details>

<details>
<summary>10. Why shouldn't you size a process pool with `os.cpu_count()` inside a Kubernetes pod or container?</summary>

For example, `os.cpu_count()` returns the logical CPUs of the physical host node, such as `128` on a dual-socket GPU server. It ignores the container's cgroup limit, such as `resources.limits.cpu: "4"`. Starting 128 workers inside a 4-CPU container causes heavy context-switch thrashing and CFS bandwidth throttling, which shows up as `nr_throttled` in `/sys/fs/cgroup/cpu.stat`. Use **`len(os.sched_getaffinity(0))`** or read the cgroup `cpu.max` file instead. When you use process pools, also set `OMP_NUM_THREADS=1` and `MKL_NUM_THREADS=1`, so that native BLAS libraries do not oversubscribe the cores.
</details>

<details>
<summary>11. How does the `asyncio` event loop achieve high concurrency on a single thread, and why must you hold a reference to `asyncio.create_task(coro)`?</summary>

The event loop multiplexes thousands of lightweight coroutine tasks on **one OS thread**. It uses non-blocking sockets and OS readiness notification, `epoll` on Linux or `kqueue` on macOS. Calling an `async def` function only returns a coroutine object. **`asyncio.create_task(coro)`** wraps that object in a `Task` and schedules it. The loop holds only **weak references** to tasks. So a fire-and-forget task whose result is not saved in a variable or a set can be garbage collected while it runs.
</details>

<details>
<summary>12. Compare `asyncio.gather(*aws, return_exceptions=...)`, `asyncio.as_completed(aws)`, and Python 3.11+ `asyncio.TaskGroup()`.</summary>

- **`asyncio.gather(*aws, return_exceptions=True)`** runs awaitables concurrently and returns results in input order. With `return_exceptions=True`, exceptions come back as values in the result list. With `return_exceptions=False`, the first exception reaches the caller at once, while the remaining tasks keep running in the background as orphans.
- **`asyncio.as_completed(aws)`**, yields each future or coroutine in completion order, as it finishes.
- **`async with asyncio.TaskGroup() as tg:`** gives you structured concurrency. Every task you add with `tg.create_task(...)` is awaited before the block exits. If one task raises an unhandled exception, the group cancels its sibling tasks, waits for their cleanup, and raises an `ExceptionGroup`, which you handle with `except*`.
</details>

<details>
<summary>13. How do `asyncio.wait_for(coro, timeout)` / `asyncio.timeout(10)` and `CancelledError` interact?</summary>

When the timeout expires in `await asyncio.wait_for(coro, timeout=10)` or `async with asyncio.timeout(10):`, `asyncio` calls **`task.cancel()`** on the inner task. It raises **`asyncio.CancelledError`** at the current `await`, waits for the `finally:` blocks to finish, and then raises `TimeoutError` to the caller. If your coroutine catches `except Exception:`, or uses a bare `except:` or `except BaseException:`, without re-raising `CancelledError`, you break timeouts and `TaskGroup` cancellation. In Python 3.8 and later, `CancelledError` inherits from `BaseException`, not `Exception`. Use `asyncio.shield(coro)` only when an operation must not be interrupted mid-flight.
</details>

<details>
<summary>14. Why do you wrap a blocking file write in `await asyncio.to_thread(save, data, path)`, and what happens if you call `time.sleep` or `requests.get` inside a coroutine?</summary>

Synchronous blocking calls, such as `time.sleep()`, `requests.get()`, `subprocess.run()` or a blocking disk write, freeze every other task on the single event-loop thread. Under `PYTHONASYNCIODEBUG=1`, they also trigger `Executing <Task ...> took 0.XXX seconds` warnings. Standard `asyncio` has no native file I/O API. So **`await asyncio.to_thread(save, data, path)`**, or `loop.run_in_executor(None, ...)`, sends the blocking function to asyncio's default `ThreadPoolExecutor`. That releases the GIL during disk and network I/O, and the loop keeps running while you await the result.
</details>

<details>
<summary>15. How do Asynchronous Iterators (`__aiter__`/`__anext__`), Asynchronous Generators (`async def` + `yield`), and PEP 530 Asynchronous Comprehensions work?</summary>

- **Async iterator (`AsyncRange`):** `__aiter__(self)` returns the iterator. `async def __anext__(self)` awaits any I/O, then returns the next item, or raises **`StopAsyncIteration`** when none remain.
- **Async generator (`multi_probe`):** Any `async def` function that contains `yield` returns an `AsyncGenerator`. You consume it with **`async for item in aiter:`**.
- **PEP 530 async comprehensions:** `[x async for x in aiter if cond]` and `{k: v async for k, v in multi_probe(names)}` consume async iterables. Inside an `async def` function, `[await probe(n) for n in names]` awaits coroutines in any comprehension.
</details>

<details>
<summary>16. How do you bound concurrency and memory in an `asyncio` service or fleet fan-out (`Semaphore` and bounded `asyncio.Queue` worker pool)?</summary>

1. **For a known list of targets:** Create `sem = asyncio.Semaphore(100)`, and wrap each request in `async with sem: return await fetch(h)`. That way, at most 100 sockets are open at once.
2. **For streaming or huge inputs, as in `run_pool`:** Create a bounded **`q = asyncio.Queue(maxsize=500)`**, and start a fixed number of worker tasks, here `concurrency=50`. Each worker loops on `item = await q.get()` inside a `try:` block, with `finally: q.task_done()`. When the workers fall behind, `await q.put(item)` suspends the producer. That is backpressure, and it keeps memory flat at `O(queue_size + concurrency)`.
</details>

<details>
<summary>17. Why do synchronized retries cause a "Retry Storm" (Thundering Herd), and how does Exponential Backoff with Full Jitter prevent it?</summary>

If 1,000 clients hit a briefly overloaded API or BMC switch, and all retry at fixed intervals such as `1s`, `2s`, `4s` and `8s`, they all hit the recovering server in the same millisecond, wave after wave. **Exponential backoff with full jitter** computes `delay = random.uniform(0, min(cap, base * 2 ** attempt))`. That spreads retries across `[0, cap]`, which smooths the load while the failed targets recover. Per-host or per-rack semaphores and circuit breakers help as well.
</details>

<details>
<summary>18. How do you bridge Threads and Asyncio safely (`to_thread`, `run_in_executor`, `run_coroutine_threadsafe`)?</summary>

- **From an `asyncio` coroutine to a blocking thread or process:** Use **`await asyncio.to_thread(fn, *args)`** for blocking I/O, or **`await loop.run_in_executor(process_pool, cpu_fn, *args)`** for CPU-bound work.
- **From an outside OS thread into a running event loop:** `asyncio` objects such as `Loop`, `Task`, `Queue` and `Event` are not thread-safe. Never call `loop.create_task()` or `q.put_nowait()` directly from another thread. Instead, use **`fut = asyncio.run_coroutine_threadsafe(coro, loop)`**, which returns a thread-safe `concurrent.futures.Future`, or `loop.call_soon_threadsafe(callback, *args)`.
</details>

<details>
<summary>19. How do production Python web/API servers (`uvicorn`, `gunicorn`, FastAPI) combine processes, threads, and `asyncio`?</summary>

The GIL binds one Python process to one core for bytecode. Production ASGI deployments run one worker process per CPU core, such as `gunicorn -k uvicorn.workers.UvicornWorker -w N` or `uvicorn --workers N`, or several Kubernetes Pod replicas. Each process runs its own `asyncio` event loop, often accelerated by `uvloop`, that handles thousands of concurrent I/O connections. Blocking calls go to the process's local thread pool, through `to_thread` or FastAPI `def` endpoints. State is shared across workers through external stores such as `Redis` or `PostgreSQL`.
</details>

<details>
<summary>20. How do you diagnose a hung multi-threaded or `asyncio` Python process in production without restarting it?</summary>

1. **`py-spy dump --pid <PID>`** (or `py-spy top`) samples the live process from outside and prints the call stack of every thread, with no code changes.
2. **`faulthandler`**: enable it with `faulthandler.enable()` and `faulthandler.register(signal.SIGUSR1)` at startup. Then `kill -SIGUSR1 <PID>` dumps every thread's stack to `stderr`. You can also use `faulthandler.dump_traceback_later(60, repeat=True)`.
3. **`asyncio` debug mode:** Run with `PYTHONASYNCIODEBUG=1`, or with `asyncio.run(main(), debug=True)`. It logs callbacks that take longer than `100 ms`, un-awaited coroutines and pending tasks, which you can list with `asyncio.all_tasks()`.
</details>

## Sources and review notes

- **Sources used:**
  - Luciano Ramalho, *Fluent Python*, 2nd ed.: Chapter 19 (concurrency models, the GIL and process pools), Chapter 20 (concurrent executors, `map` ordering and `as_completed`) and Chapter 21 (asynchronous programming, semaphores, `to_thread`, async generators).
  - Mark Lutz, *Learning Python*, 6th ed., Chapter 20: asynchronous iterators and comprehensions.
  - `nvidia-devops` volume 2, Python systems concurrency masterclass: concurrency model selection, `ThreadPoolExecutor` fan-out and backpressure, and retries with full jitter.
- **Corrections in the rework:** The Linux default start method in Python 3.14 is `forkserver`, not `spawn` (What's New in Python 3.14, multiprocessing). Thread safety is no longer claimed for paramiko and database connections; only the low-level boto3 client is documented as thread-safe, and the DB-API `threadsafety` attribute is the check for drivers. The aiohttp example now imports the library and passes `aiohttp.ClientTimeout`. The retry example imports `random`. Author-laptop timings from the book demos were removed. The new experiment gives no numbers on purpose.
- **Not re-checked:** The aiohttp timeout behaviour was checked from memory against the aiohttp client documentation, not against a pinned version.
- **Run here:** `python3 code/part03/python_concurrency_models_lab.py` (4 passed, 0 failed).
- **Explicitly labelled inferences:** The Section 2 `bounded_map`, Section 4 `run_pool` worker-pool template, and Section 5 `retry` with full jitter are the author's constructions applying the book patterns to fleet-scale infrastructure automation.
- **Not verified on live hardware:** Fleet-scale benchmarks (`5,000` BMCs, `800` nodes, `10 million` objects, `10,000` servers, `5 TB` dataset, `python3.13t` PEP 703, `3.14` PEP 684/734 subinterpreters) were not run live, apart from what is executed by `python_concurrency_models_lab.py`.
