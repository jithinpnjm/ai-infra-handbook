"""Measure the hidden costs of common Python operations with timeit.

Each function returns seconds (best of several repeats, as the timeit
documentation advises). Run this file to print a table for your machine.
"""
import sys
import timeit
from collections import deque


def best(stmt, setup="pass", number=1, repeat=5, globals_=None):
    """Smallest total time over `repeat` runs of `number` executions."""
    return min(timeit.repeat(stmt, setup=setup, number=number, repeat=repeat,
                             globals=globals_))


def membership(n, probes=200):
    """Time `probes` lookups of the worst-case item in a list and in a set."""
    data_list = list(range(n))
    data_set = set(data_list)
    g = {"L": data_list, "S": data_set, "x": n - 1}
    t_list = best("for _ in range(%d): x in L" % probes, number=1, globals_=g)
    t_set = best("for _ in range(%d): x in S" % probes, number=1, globals_=g)
    return t_list, t_set


def front_insert(n, ops=2000):
    """Insert `ops` items at the front of a list of size n versus a deque."""
    g = {"base": list(range(n)), "deque": deque}
    t_list = best("L = list(base)\nfor i in range(%d): L.insert(0, i)" % ops,
                  number=1, repeat=3, globals_=g)
    t_deque = best("D = deque(base)\nfor i in range(%d): D.appendleft(i)" % ops,
                   number=1, repeat=3, globals_=g)
    return t_list, t_deque


def concat(n):
    """Build a string from n pieces with += versus join."""
    g = {"n": n}
    t_plus = best("s = ''\nfor i in range(n): s += 'ab'", number=1, globals_=g)
    t_join = best("s = ''.join(['ab' for i in range(n)])", number=1, globals_=g)
    return t_plus, t_join


def concat_shared(n):
    """Same += loop, but a second reference to the string defeats CPython's
    in-place resize, so every step copies the whole string."""
    g = {"n": n}
    return best("s = ''\nfor i in range(n):\n    keep = s\n    s += 'ab'",
                number=1, repeat=3, globals_=g)


def sort_cost(n):
    """sorted() on random data versus on data that is already sorted."""
    import random
    rnd = random.Random(0)
    data = [rnd.random() for _ in range(n)]
    srt = sorted(data)
    g = {"R": data, "S": srt}
    return best("sorted(R)", globals_=g), best("sorted(S)", globals_=g)


def growth_points(limit=64):
    """Sizes at which a list's allocation changes while appending."""
    lst, last, points = [], sys.getsizeof([]), []
    for i in range(limit):
        lst.append(i)
        size = sys.getsizeof(lst)
        if size != last:
            points.append((len(lst), size))
            last = size
    return points


if __name__ == "__main__":
    print(sys.version.split()[0], sys.platform)
    for n in (1_000, 100_000):
        a, b = membership(n)
        print(f"membership n={n:>7}: list {a*1e6/200:9.2f} us, set {b*1e6/200:7.3f} us per lookup")
    for n in (1_000, 100_000):
        a, b = front_insert(n)
        print(f"front insert n={n:>7}: list {a*1e6/2000:8.2f} us, deque {b*1e6/2000:6.3f} us per op")
    for n in (10_000, 200_000):
        a, b = concat(n)
        print(f"concat n={n:>7}: += {a*1e3:8.2f} ms, join {b*1e3:8.2f} ms")
    for n in (10_000, 40_000):
        print(f"concat with a second reference n={n:>6}: += {concat_shared(n)*1e3:8.2f} ms")
    a, b = sort_cost(1_000_000)
    print(f"sorted 1M floats: random {a*1e3:7.1f} ms, already sorted {b*1e3:7.1f} ms")
    print("append growth (length, bytes):", growth_points())
