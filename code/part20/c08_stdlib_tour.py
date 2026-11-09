# code/part20/c08_stdlib_tour.py
"""Exact behaviours of the standard-library tools worth knowing (chapter 20.8)."""
import bisect
import heapq
import re
import statistics
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import accumulate, groupby, islice, pairwise, product


def counter_demo():
    c = Counter("abracadabra")
    return c.most_common(2), c["z"], Counter("ab") + Counter("bc")


def defaultdict_demo():
    d = defaultdict(list)
    d["x"].append(1)
    _ = d["missing"]            # merely reading creates the key
    return dict(d)


def deque_demo():
    q = deque([1, 2, 3], maxlen=3)
    q.append(4)                  # drops 1 from the left
    q.appendleft(0)              # drops 4 from the right
    return list(q)


def heap_demo():
    h = [5, 1, 4]
    heapq.heapify(h)             # min-heap
    smallest = heapq.heappop(h)
    top2 = heapq.nlargest(2, [5, 1, 4, 9])
    max_heap = [-x for x in (5, 1, 4)]
    heapq.heapify(max_heap)
    return smallest, top2, -heapq.heappop(max_heap)


def bisect_demo():
    a = [1, 2, 2, 2, 5]
    return bisect.bisect_left(a, 2), bisect.bisect_right(a, 2), bisect.bisect_left(a, 3)


def itertools_demo():
    return (
        list(accumulate([1, 2, 3, 4])),
        list(pairwise("abcd")),
        list(islice(range(100), 3)),
        len(list(product("ab", repeat=3))),
        [(k, len(list(g))) for k, g in groupby("aabbbc")],
    )


@lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)


def cache_info_demo():
    fib.cache_clear()
    value = fib(30)
    return value, fib.cache_info().misses


@dataclass(order=True, frozen=True)
class Job:
    priority: int
    name: str = field(compare=False)


def dataclass_demo():
    jobs = [Job(2, "b"), Job(1, "a")]
    return min(jobs).name, Job(1, "x") == Job(1, "y")


def regex_demo():
    line = '10.0.0.7 - GET /v1/chat 503 12ms'
    m = re.search(r"(?P<ip>\d+\.\d+\.\d+\.\d+) .* (?P<code>\d{3}) (?P<ms>\d+)ms", line)
    return m.group("ip"), m.group("code"), int(m.group("ms")), re.findall(r"\d+", "a1b22c333")


def statistics_demo():
    data = [1, 2, 3, 4, 100]
    return (
        statistics.mean(data),
        statistics.median(data),
        statistics.median([1, 2, 3, 4]),
        statistics.quantiles(data, n=4),
    )
