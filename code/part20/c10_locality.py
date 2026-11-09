"""Sequential versus shuffled access over the same data, in pure Python.

Shows that visiting memory in a scattered order costs time even in Python.
The array holds raw 8-byte values, so the shuffled walk jumps across memory.
"""
import random
import timeit
from array import array


def make(n, seed=0):
    data = array("q", range(n))
    order = list(range(n))
    random.Random(seed).shuffle(order)
    return data, order


def sum_in_order(data, order):
    total = 0
    for i in range(len(order)):
        total += data[i]
    return total


def sum_shuffled(data, order):
    total = 0
    for i in order:
        total += data[i]
    return total


def measure(n=5_000_000, repeat=3):
    data, order = make(n)
    seq = min(timeit.repeat(lambda: sum_in_order(data, order), number=1, repeat=repeat))
    shuf = min(timeit.repeat(lambda: sum_shuffled(data, order), number=1, repeat=repeat))
    return seq, shuf


if __name__ == "__main__":
    seq, shuf = measure()
    print(f"5M items sequential {seq:.3f} s, shuffled {shuf:.3f} s, ratio {shuf/seq:.2f}")
