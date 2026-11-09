# code/part20/c08_pitfalls.py
"""Python traps that cost points in a live coding round (chapter 20.8). Each returns a value you can assert."""
import sys


def append_bad(x, bucket=[]):
    bucket.append(x)
    return bucket


def append_good(x, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(x)
    return bucket


def division_demo():
    return 7 / 2, 7 // 2, -7 // 2, -7 % 3


def aliased_grid():
    grid = [[0] * 2] * 2          # two names for one row
    grid[0][0] = 1
    return grid


def real_grid():
    grid = [[0] * 2 for _ in range(2)]
    grid[0][0] = 1
    return grid


def slice_is_a_copy():
    data = list(range(5))
    part = data[1:4]
    part[0] = 99
    return data, part


def depth(n):
    return 0 if n == 0 else 1 + depth(n - 1)


def recursion_fails_at(limit_probe=5000):
    try:
        depth(limit_probe)
    except RecursionError:
        return True
    return False


def default_recursion_limit():
    return sys.getrecursionlimit()


def float_traps():
    import math
    return 0.1 + 0.2 == 0.3, math.isclose(0.1 + 0.2, 0.3)


def sort_is_stable():
    rows = [("b", 1), ("a", 1), ("c", 0)]
    return sorted(rows, key=lambda r: r[1])


def dict_keeps_insertion_order():
    d = {}
    d["z"], d["a"] = 1, 2
    return list(d), {"a": 1, "z": 2} == {"z": 2, "a": 1}


def mutate_while_iterating():
    items = [2, 4, 6, 8]
    for x in items:
        if x % 2 == 0:
            items.remove(x)
    return items


def groupby_without_sorting():
    from itertools import groupby
    return [(k, len(list(g))) for k, g in groupby("aabaa")]
