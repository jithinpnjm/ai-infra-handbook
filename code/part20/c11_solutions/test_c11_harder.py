"""Tests for the eight harder problems (H1-H8)."""
import itertools
import random

import pytest

from c11_h01_lfu_cache import LFUCache
from c11_h02_sliding_max import sliding_max
from c11_h03_sliding_median import sliding_median
from c11_h04_cheapest_route import cheapest_route
from c11_h05_edit_distance import edit_distance
from c11_h06_gpu_pack import gpu_pack
from c11_h07_failure_clusters import FailureClusters
from c11_h08_path_router import Router

RNG = random.Random(13)


class LFUModel:
    """Brute force: scan for the minimum (frequency, last-use tick)."""

    def __init__(self, cap):
        self.cap, self.d, self.tick = cap, {}, 0

    def get(self, k):
        self.tick += 1
        if k not in self.d:
            return None
        v, f, _ = self.d[k]
        self.d[k] = (v, f + 1, self.tick)
        return v

    def put(self, k, v):
        self.tick += 1
        if k in self.d:
            self.d[k] = (v, self.d[k][1] + 1, self.tick)
            return
        if len(self.d) >= self.cap:
            victim = min(self.d, key=lambda x: (self.d[x][1], self.d[x][2]))
            del self.d[victim]
        self.d[k] = (v, 1, self.tick)


def test_h01():
    c = LFUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)  # evicts 2 (freq 1)
    assert c.get(2) is None
    assert c.get(3) == 3
    c.put(4, 4)  # 1 and 3 tie on freq 2; 1 is older -> evict 1
    assert c.get(1) is None and c.get(3) == 3 and c.get(4) == 4
    with pytest.raises(ValueError):
        LFUCache(0)
    for _ in range(300):
        cap = RNG.randint(1, 4)
        real, model = LFUCache(cap), LFUModel(cap)
        for _ in range(80):
            k = RNG.randint(0, 6)
            if RNG.random() < 0.5:
                v = RNG.randint(0, 9)
                real.put(k, v)
                model.put(k, v)
            else:
                assert real.get(k) == model.get(k)
            assert len(real) == len(model.d)


def test_h02():
    assert sliding_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert sliding_max([], 2) == []
    assert sliding_max([5], 1) == [5]
    assert sliding_max([1, 2], 3) == []
    with pytest.raises(ValueError):
        sliding_max([1], 0)
    for _ in range(400):
        xs = [RNG.randint(-5, 5) for _ in range(RNG.randint(0, 14))]
        k = RNG.randint(1, 6)
        assert sliding_max(xs, k) == [max(xs[i:i + k]) for i in range(len(xs) - k + 1)]


def test_h03():
    assert sliding_median([1, 3, -1, -3, 5, 3, 6, 7], 3) == [1, -1, -1, 3, 5, 6]
    assert sliding_median([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]
    assert sliding_median([2, 2, 2, 2], 2) == [2, 2, 2]
    assert sliding_median([9], 1) == [9]
    assert sliding_median([1], 2) == []
    with pytest.raises(ValueError):
        sliding_median([1], 0)
    for _ in range(1500):
        xs = [RNG.randint(-4, 4) for _ in range(RNG.randint(0, 16))]
        k = RNG.randint(1, 7)
        brute = []
        for i in range(len(xs) - k + 1):
            w = sorted(xs[i:i + k])
            brute.append(w[k // 2] if k % 2 else (w[k // 2 - 1] + w[k // 2]) / 2)
        assert sliding_median(xs, k) == brute


def test_h04():
    edges = [(0, 1, 100), (1, 2, 100), (0, 2, 500)]
    assert cheapest_route(3, edges, 0, 2, 1) == 200
    assert cheapest_route(3, edges, 0, 2, 0) == 500
    assert cheapest_route(3, [(0, 1, 5)], 0, 2, 3) == -1
    assert cheapest_route(2, [], 0, 0, 0) == 0
    for _ in range(300):
        n = RNG.randint(2, 5)
        es = [(RNG.randrange(n), RNG.randrange(n), RNG.randint(0, 9)) for _ in range(RNG.randint(0, 9))]
        k = RNG.randint(0, 3)
        best = float("inf")

        def dfs(u, cost, edges_left):
            nonlocal best
            if u == 3 % n:
                best = min(best, cost)
            if edges_left == 0:
                return
            for a, b, c in es:
                if a == u:
                    dfs(b, cost + c, edges_left - 1)

        dfs(0, 0, k + 1)
        assert cheapest_route(n, es, 0, 3 % n, k) == (best if best != float("inf") else -1)


def test_h05():
    assert edit_distance("kitten", "sitting") == 3
    assert edit_distance("", "abc") == 3
    assert edit_distance("abc", "") == 3
    assert edit_distance("", "") == 0
    assert edit_distance("same", "same") == 0
    from functools import lru_cache

    for _ in range(300):
        a = "".join(RNG.choice("ab") for _ in range(RNG.randint(0, 6)))
        b = "".join(RNG.choice("ab") for _ in range(RNG.randint(0, 6)))

        @lru_cache(None)
        def f(i, j):
            if i == len(a):
                return len(b) - j
            if j == len(b):
                return len(a) - i
            if a[i] == b[j]:
                return f(i + 1, j + 1)
            return 1 + min(f(i + 1, j), f(i, j + 1), f(i + 1, j + 1))

        assert edit_distance(a, b) == f(0, 0)
        assert edit_distance(a, b) == edit_distance(b, a)


def test_h06():
    assert gpu_pack([10, 20, 30], [60, 100, 120], 50) == (220, [1, 2])
    assert gpu_pack([5], [10], 4) == (0, [])
    assert gpu_pack([], [], 10) == (0, [])
    assert gpu_pack([3], [7], 0) == (0, [])
    for _ in range(300):
        n = RNG.randint(0, 8)
        mem = [RNG.randint(1, 6) for _ in range(n)]
        val = [RNG.randint(0, 9) for _ in range(n)]
        cap = RNG.randint(0, 15)
        best = max(sum(val[i] for i in s) for r in range(n + 1) for s in itertools.combinations(range(n), r)
                   if sum(mem[i] for i in s) <= cap)
        got, chosen = gpu_pack(mem, val, cap)
        assert got == best
        assert sum(mem[i] for i in chosen) <= cap and sum(val[i] for i in chosen) == got


def test_h07():
    fc = FailureClusters()
    assert fc.clusters == 0 and fc.largest == 0 and fc.size_of("x") == 0
    assert fc.link("a", "b") is True
    assert fc.link("b", "a") is False
    fc.add("z")
    assert fc.clusters == 2 and fc.largest == 2
    fc.link("c", "d")
    fc.link("b", "c")
    assert fc.size_of("d") == 4 and fc.clusters == 2 and fc.largest == 4
    for _ in range(200):
        fc, edges, nodes = FailureClusters(), [], set()
        for _ in range(RNG.randint(0, 20)):
            a, b = RNG.randint(0, 9), RNG.randint(0, 9)
            fc.link(a, b)
            edges.append((a, b))
            nodes |= {a, b}
            adj = {n: set() for n in nodes}
            for u, v in edges:
                adj[u].add(v)
                adj[v].add(u)
            seen, sizes = set(), []
            for n in nodes:
                if n in seen:
                    continue
                stack, comp = [n], 0
                seen.add(n)
                while stack:
                    u = stack.pop()
                    comp += 1
                    for w in adj[u] - seen:
                        seen.add(w)
                        stack.append(w)
                sizes.append(comp)
            assert fc.clusters == len(sizes) and fc.largest == max(sizes)


def test_h08():
    r = Router()
    r.add("/v1/models/*/infer", "infer")
    r.add("/v1/models/llama/infer", "llama-infer")
    r.add("/v1/*/health", "health")
    r.add("/", "root")
    assert r.match("/v1/models/llama/infer") == "llama-infer"
    assert r.match("/v1/models/other/infer") == "infer"
    assert r.match("/v1/models/health") == "health"
    assert r.match("/v1/x/health") == "health"
    assert r.match("/v1/models/llama/health") is None
    assert r.match("/") == "root" and r.match("") == "root"
    assert r.match("/v1/models/x//infer/") == "infer"  # empty segments are ignored
    # backtracking: static branch dead-ends, wildcard branch still matches
    r2 = Router()
    r2.add("/a/b/c", "static")
    r2.add("/a/*/d", "wild")
    assert r2.match("/a/b/d") == "wild"
    # brute force: all matching routes, smallest priority tuple wins
    for _ in range(300):
        segs = ["a", "b", "*"]
        routes = {}
        r3 = Router()
        for i in range(RNG.randint(0, 6)):
            pat = "/" + "/".join(RNG.choice(segs) for _ in range(RNG.randint(1, 3)))
            routes[pat] = f"h{i}"
            r3.add(pat, f"h{i}")
        for _ in range(10):
            path = "/" + "/".join(RNG.choice("ab") for _ in range(RNG.randint(1, 3)))
            ps = path.split("/")[1:]
            cand = []
            for pat, h in routes.items():
                pp = pat.split("/")[1:]
                if len(pp) == len(ps) and all(x == "*" or x == y for x, y in zip(pp, ps)):
                    cand.append(([0 if x != "*" else 1 for x in pp], h))
            assert r3.match(path) == (min(cand)[1] if cand else None)
