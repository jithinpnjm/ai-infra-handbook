"""Consistent hashing with virtual nodes, plus the balance and movement measurements."""
import bisect
import hashlib
from collections import Counter


def h(s):
    """Stable 64-bit hash. Python's built-in hash() changes between processes, so never use it."""
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], "big")


class Ring:
    def __init__(self, nodes=(), vnodes=100):
        self.vnodes = vnodes
        self.points = []     # sorted hashes
        self.owner = {}      # hash -> node
        for n in nodes:
            self.add(n)

    def add(self, node):
        for i in range(self.vnodes):
            p = h(f"{node}#{i}")
            if p not in self.owner:
                bisect.insort(self.points, p)
                self.owner[p] = node

    def remove(self, node):
        keep = [p for p in self.points if self.owner[p] != node]
        self.owner = {p: self.owner[p] for p in keep}
        self.points = keep

    def lookup(self, key):
        if not self.points:
            raise LookupError("empty ring")
        i = bisect.bisect_right(self.points, h(key))
        return self.owner[self.points[i % len(self.points)]]   # wrap around the circle


def balance(ring, keys):
    """Return (max load / mean load, counts per node)."""
    counts = Counter(ring.lookup(k) for k in keys)
    mean = len(keys) / len(counts)
    return max(counts.values()) / mean, counts


def moved_fraction(before, after, keys):
    return sum(before.lookup(k) != after.lookup(k) for k in keys) / len(keys)


def modulo_moved_fraction(n_before, n_after, keys):
    return sum(h(k) % n_before != h(k) % n_after for k in keys) / len(keys)
