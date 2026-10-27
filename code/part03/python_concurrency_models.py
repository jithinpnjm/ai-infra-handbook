"""Chapter 3.6 model: Concurrency models in Python (threads, multiprocessing,
concurrent.futures executors, and asyncio).

Sources modeled:
- Luciano Ramalho, Fluent Python, 2nd ed. (fluent-python-2nd-edition, FP):
  * Chapter 19 ("Concurrency Models in Python"): Rob Pike's concurrency vs
    parallelism definition, spinner_thread.py (threading.Thread + Event.wait),
    spinner_proc.py (multiprocessing.Process + Event), spinner_async.py
    (asyncio.create_task + Task.cancel + CancelledError), CPU-bound is_prime(n)
    across NUMBERS (2 to 9,999,999,999,999,999) with procs.py SimpleQueue poison-pill
    workers vs sequential.py, and WSGI/ASGI deployment models.
  * Chapter 20 ("Concurrent Executors"): flags.py vs flags_threadpool.py
    (Executor.map) vs flags2_threadpool.py (executor.submit + as_completed +
    to_do_map dict + Counter), and proc_pool.py ProcessPoolExecutor.map ordered
    output waiting on 9999999999999917.
  * Chapter 21 ("Asynchronous Programming"): blogdom.py / domainlib.py
    (loop.getaddrinfo, asyncio.as_completed, multi_probe async generator, async
    comprehensions PEP 530), flags_asyncio.py / flags2_asyncio.py (asyncio.Semaphore
    concur_req, httpx.AsyncClient, asyncio.to_thread for save_flag), and
    tcp_mojifinder.py / web_mojifinder.py.
- Mark Lutz, Learning Python, 6th ed. (learning-python-6th-edition, LP):
  * Chapter 20 ("Comprehensions and Generations"): all_async_demos.py comparing
    serial time.sleep vs async def producer/consumer with asyncio.sleep,
    asyncio.gather(*tasks), and AsyncRange (__aiter__/__anext__ with async for).
- volume-02/02-python-systems-concurrency-masterclass.md.
"""
import asyncio
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, as_completed, wait
from itertools import islice
import math
import threading
from typing import AsyncIterator, Callable, Dict, Iterable, Iterator, List, NamedTuple, Sequence, Tuple


def is_prime(n: int) -> bool:
    """FP Ch. 19 Example 19-4 primes.py: CPU-bound primality check."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    root = math.isqrt(n)
    for i in range(3, root + 1, 2):
        if n % i == 0:
            return False
    return True


class PrimeResult(NamedTuple):
    n: int
    prime: bool


def run_threadpool_to_do_map(
    items: Sequence[int],
    fail_on: int = -1,
    max_workers: int = 4,
) -> Tuple[Dict[int, bool], Dict[int, str]]:
    """FP Ch. 20 Example 20-16 flags2_threadpool.py pattern: map each Future to
    its input key in `to_do_map`, consume via `as_completed(to_do_map)`, and
    isolate per-item exceptions.
    """
    results: Dict[int, bool] = {}
    errors: Dict[int, str] = {}

    def _task(n: int) -> bool:
        if n == fail_on:
            raise ValueError(f"simulated error on {n}")
        return is_prime(n)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        to_do_map = {executor.submit(_task, n): n for n in items}
        for future in as_completed(to_do_map):
            n = to_do_map[future]
            try:
                results[n] = future.result()
            except Exception as exc:
                errors[n] = type(exc).__name__
    return results, errors


def bounded_map(
    fn: Callable[[int], int],
    iterable: Iterable[int],
    *,
    workers: int = 4,
    max_inflight: int = 8,
) -> Iterator[int]:
    """Section 2 backpressure helper: keep at most `max_inflight` futures alive."""
    it = iter(iterable)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        inflight = {pool.submit(fn, x) for x in islice(it, max_inflight)}
        while inflight:
            done, inflight = wait(inflight, return_when=FIRST_COMPLETED)
            for fut in done:
                yield fut.result()
            for x in islice(it, len(done)):
                inflight.add(pool.submit(fn, x))


def run_thread_spinner_demo() -> Tuple[int, bool]:
    """FP Ch. 19 Example 19-1 spinner_thread.py: coordinate a background thread via threading.Event."""
    done = threading.Event()
    ticks = 0

    def spin() -> None:
        nonlocal ticks
        while not done.wait(0.001):
            ticks += 1

    spinner = threading.Thread(target=spin)
    spinner.start()
    done.set()
    spinner.join(timeout=1.0)
    return ticks, not spinner.is_alive()


async def run_async_spinner_cancellation_demo() -> Tuple[int, bool]:
    """FP Ch. 19 Example 19-3 spinner_async.py: cancel a background Task and catch CancelledError."""
    cancelled_cleanly = False

    async def spin() -> None:
        nonlocal cancelled_cleanly
        try:
            while True:
                await asyncio.sleep(0.001)
        except asyncio.CancelledError:
            cancelled_cleanly = True
            raise

    spinner = asyncio.create_task(spin())
    await asyncio.sleep(0.005)
    spinner.cancel()
    try:
        await spinner
    except asyncio.CancelledError:
        pass
    return 42, cancelled_cleanly


class AsyncRange:
    """LP Ch. 20 all_async_demos.py: Async iterable implementing __aiter__ and __anext__."""

    def __init__(self, start: int, stop: int) -> None:
        self.start = start
        self.stop = stop

    def __aiter__(self) -> "AsyncRange":
        self.cur = self.start
        return self

    async def __anext__(self) -> int:
        if self.cur >= self.stop:
            raise StopAsyncIteration
        await asyncio.sleep(0)
        val = self.cur
        self.cur += 1
        return val


async def multi_probe_async_gen(names: Iterable[str]) -> AsyncIterator[Tuple[str, bool]]:
    """FP Ch. 21 Example 21-18 domainlib.py: Async generator yielding results as
    tasks complete via asyncio.as_completed.
    """
    async def probe(name: str) -> Tuple[str, bool]:
        await asyncio.sleep(0.001)
        return name, name.endswith(".org")

    coros = [probe(name) for name in names]
    for coro in asyncio.as_completed(coros):
        result = await coro
        yield result


async def run_async_semaphore_and_comprehension_demo() -> Dict[str, object]:
    """FP Ch. 21 & LP Ch. 20: Bounded Semaphore fan-out, async comprehension
    (PEP 530), AsyncRange, and asyncio.to_thread offloading.
    """
    sem = asyncio.Semaphore(2)
    active = 0
    max_active = 0

    async def fetch_bounded(x: int) -> int:
        nonlocal active, max_active
        async with sem:
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0.002)
            # Offload blocking function via asyncio.to_thread (FP Ch. 21 save_flag)
            res = await asyncio.to_thread(lambda v: v * 2, x)
            active -= 1
            return res

    gathered = await asyncio.gather(*(fetch_bounded(i) for i in range(6)))
    domains = ["python.org", "rust-lang.org", "invalid.local"]
    found_dict = {name: ok async for name, ok in multi_probe_async_gen(domains)}
    async_range_vals = [x ** 2 async for x in AsyncRange(1, 5)]

    return {
        "gathered": gathered,
        "max_active": max_active,
        "found_dict": found_dict,
        "async_range_vals": async_range_vals,
    }
