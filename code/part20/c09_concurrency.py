"""Basic concurrency: producer/consumer, a thread-safe counter, asyncio gather with timeouts."""
import asyncio
import queue
import threading

SENTINEL = object()


def run_pipeline(items, n_workers, work):
    """Producer puts items on a bounded queue. n_workers consumers apply work().

    Each worker gets one sentinel so it knows when to stop. Returns results in completion order.
    """
    q = queue.Queue(maxsize=10)          # bounded: a slow consumer slows the producer
    results, lock = [], threading.Lock()

    def worker():
        while True:
            item = q.get()
            if item is SENTINEL:
                return
            r = work(item)
            with lock:
                results.append(r)

    threads = [threading.Thread(target=worker) for _ in range(n_workers)]
    for t in threads:
        t.start()
    for it in items:
        q.put(it)
    for _ in threads:
        q.put(SENTINEL)
    for t in threads:
        t.join()
    return results


class Counter:
    """`self.n += 1` is read, add, write: three steps. Without the lock updates can be lost."""

    def __init__(self):
        self.n = 0
        self._lock = threading.Lock()

    def inc(self):
        with self._lock:
            self.n += 1


class UnsafeCounter:
    def __init__(self):
        self.n = 0

    def inc(self):
        self.n += 1


def hammer(counter, threads=8, per_thread=20_000):
    ts = [threading.Thread(target=lambda: [counter.inc() for _ in range(per_thread)])
          for _ in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return counter.n


async def fetch_all(fns, per_call_timeout, overall_timeout):
    """Run coroutine functions concurrently. Return a list of ('ok', value) or ('err', name).

    A slow call times out alone. The overall budget cancels whatever is still running.
    """
    async def one(fn):
        try:
            return ("ok", await asyncio.wait_for(fn(), per_call_timeout))
        except asyncio.TimeoutError:
            return ("err", "timeout")
        except Exception as e:
            return ("err", type(e).__name__)

    try:
        return await asyncio.wait_for(asyncio.gather(*(one(f) for f in fns)), overall_timeout)
    except asyncio.TimeoutError:
        return [("err", "overall_timeout")] * len(fns)
