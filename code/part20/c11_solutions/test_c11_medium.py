"""Tests for the sixteen medium problems (M1-M16)."""
import itertools
import random
import re

import pytest

from c11_m01_longest_window import longest_window
from c11_m02_merge_windows import merge_windows
from c11_m03_peak_concurrency import peak_concurrency
from c11_m04_lru_cache import LRUCache
from c11_m05_kth_largest_stream import KthLargest
from c11_m06_log_templates import log_templates
from c11_m07_simplify_path import simplify_path
from c11_m08_subarray_sum import count_subarrays_with_sum
from c11_m09_lexi_toposort import CycleError, lexi_toposort
from c11_m10_min_rate import min_rate
from c11_m11_token_bucket import TokenBucket
from c11_m12_hash_ring import HashRing
from c11_m13_backoff import backoff_ceiling, backoff_schedule
from c11_m14_shortest_span import shortest_span
from c11_m15_decode_string import decode_string
from c11_m16_time_kv import TimeKV

RNG = random.Random(12)


def test_m01():
    assert longest_window([0, 1, 0, 0, 1, 1, 0], 1) == 4
    assert longest_window([], 2) == 0
    assert longest_window([1, 1, 1], 0) == 0
    assert longest_window([0, 0], 0) == 2
    with pytest.raises(ValueError):
        longest_window([0], -1)
    for _ in range(400):
        f = [RNG.randint(0, 1) for _ in range(RNG.randint(0, 12))]
        k = RNG.randint(0, 4)
        brute = max([j - i for i in range(len(f) + 1) for j in range(i, len(f) + 1) if sum(f[i:j]) <= k] or [0])
        assert longest_window(f, k) == brute


def test_m02():
    assert merge_windows([(5, 8), (1, 3), (3, 4), (2, 3)]) == [(1, 4), (5, 8)]
    assert merge_windows([]) == []
    assert merge_windows([(1, 10), (2, 3)]) == [(1, 10)]
    for _ in range(400):
        iv = []
        for _ in range(RNG.randint(0, 6)):
            s = RNG.randint(0, 12)
            iv.append((s, s + RNG.randint(1, 4)))
        cells = sorted({c for s, e in iv for c in range(s, e)})
        brute = []
        for c in cells:
            if brute and brute[-1][1] == c:
                brute[-1][1] = c + 1
            else:
                brute.append([c, c + 1])
        assert merge_windows(iv) == [tuple(x) for x in brute]


def test_m03():
    assert peak_concurrency([(1, 3), (3, 5)]) == 1  # touching jobs do not overlap
    assert peak_concurrency([(1, 4), (2, 5), (3, 6)]) == 3
    assert peak_concurrency([]) == 0
    for _ in range(400):
        jobs = []
        for _ in range(RNG.randint(0, 7)):
            s = RNG.randint(0, 10)
            jobs.append((s, s + RNG.randint(1, 5)))
        brute = max([sum(1 for s, e in jobs if s <= t < e) for t in range(0, 17)] or [0])
        assert peak_concurrency(jobs) == brute


def test_m04():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)  # evicts b
    assert c.get("b") is None and c.get("c") == 3 and c.get("a") == 1
    c.put("a", 10)  # update refreshes
    c.put("d", 4)  # evicts c
    assert c.get("c") is None and c.get("a") == 10
    with pytest.raises(ValueError):
        LRUCache(0)
    one = LRUCache(1)
    one.put(1, 1)
    one.put(2, 2)
    assert one.get(1) is None and len(one) == 1
    for _ in range(100):
        cap = RNG.randint(1, 4)
        cache, model = LRUCache(cap), []  # model: list of (k, v), oldest first
        for _ in range(60):
            k = RNG.randint(0, 5)
            if RNG.random() < 0.5:
                v = RNG.randint(0, 99)
                model = [kv for kv in model if kv[0] != k] + [(k, v)]
                model = model[-cap:]
                cache.put(k, v)
            else:
                hit = [kv for kv in model if kv[0] == k]
                if hit:
                    model = [kv for kv in model if kv[0] != k] + hit
                assert cache.get(k) == (hit[0][1] if hit else None)
            assert cache.keys_oldest_first() == [kv[0] for kv in model]


def test_m05():
    kl = KthLargest(3, [4, 5, 8, 2])
    assert kl.add(3) == 4
    assert kl.add(10) == 5
    assert KthLargest(2).add(1) is None
    with pytest.raises(ValueError):
        KthLargest(0)
    for _ in range(200):
        k = RNG.randint(1, 4)
        kl, seen = KthLargest(k), []
        for _ in range(15):
            x = RNG.randint(-5, 5)
            seen.append(x)
            expect = sorted(seen, reverse=True)[k - 1] if len(seen) >= k else None
            assert kl.add(x) == expect


def test_m06():
    lines = ["GET /user/17 took 300ms", "GET /user/9 took 5ms", "disk sda1 full"]
    assert log_templates(lines) == [("GET /user/<N> took <N>ms", 2), ("disk sda<N> full", 1)]
    assert log_templates([]) == []


def test_m07():
    assert simplify_path("/a//b/./c/../d/") == "/a/b/d"
    assert simplify_path("/../..") == "/"
    assert simplify_path("/") == "/"
    assert simplify_path("/...") == "/..."
    import posixpath
    for _ in range(500):
        parts = [RNG.choice(["a", "b", "..", ".", ""]) for _ in range(RNG.randint(0, 8))]
        p = "/" + "/".join(parts)
        assert simplify_path(p) == posixpath.normpath("/" + p.lstrip("/"))


def test_m08():
    assert count_subarrays_with_sum([1, 1, 1], 2) == 2
    assert count_subarrays_with_sum([1, -1, 0], 0) == 3
    assert count_subarrays_with_sum([], 0) == 0
    for _ in range(300):
        xs = [RNG.randint(-3, 3) for _ in range(RNG.randint(0, 10))]
        k = RNG.randint(-3, 3)
        brute = sum(1 for i in range(len(xs)) for j in range(i + 1, len(xs) + 1) if sum(xs[i:j]) == k)
        assert count_subarrays_with_sum(xs, k) == brute


def _valid_order(order, deps):
    pos = {n: i for i, n in enumerate(order)}
    return all(pos[d] < pos[s] for s, needs in deps.items() for d in needs)


def test_m09():
    deps = {"api": ["db", "cache"], "cache": [], "db": ["net"], "web": ["api"]}
    assert lexi_toposort(deps) == ["cache", "net", "db", "api", "web"]
    assert lexi_toposort({}) == []
    with pytest.raises(CycleError) as e:
        lexi_toposort({"a": ["b"], "b": ["a"], "c": []})
    assert e.value.stuck == {"a", "b"}
    for _ in range(200):
        names = list("abcdef")[: RNG.randint(1, 6)]
        deps = {}
        for i, n in enumerate(names):
            deps[n] = [m for m in names[:i] if RNG.random() < 0.4]  # only earlier names: acyclic
        shuffled = names[:]
        RNG.shuffle(shuffled)
        relabel = dict(zip(names, shuffled))
        deps2 = {relabel[n]: [relabel[m] for m in v] for n, v in deps.items()}
        brute = next(p for p in itertools.permutations(sorted(deps2)) if _valid_order(p, deps2))
        assert lexi_toposort(deps2) == list(brute)


def test_m10():
    assert min_rate([3, 6, 7, 11], 8) == 4
    assert min_rate([5], 5) == 1
    assert min_rate([], 1) == 1
    with pytest.raises(ValueError):
        min_rate([1, 2, 3], 2)
    for _ in range(300):
        sizes = [RNG.randint(1, 20) for _ in range(RNG.randint(1, 5))]
        hours = RNG.randint(len(sizes), len(sizes) * 6)
        brute = next(r for r in range(1, 21) if sum(-(-s // r) for s in sizes) <= hours)
        assert min_rate(sizes, hours) == brute


def test_m11():
    b = TokenBucket(rate=2, capacity=4, now=0)
    assert [b.allow(0) for _ in range(5)] == [True] * 4 + [False]
    assert b.allow(0.5) is True and b.allow(0.5) is False  # 0.5s -> 1 token
    assert b.wait_time(0.5) == pytest.approx(0.5)
    assert b.allow(100) and b._tokens <= 4  # refill never exceeds capacity
    b2 = TokenBucket(1, 2, now=10)
    assert b2.allow(5) is True  # clock went backwards: no refill, no crash
    assert b2.allow(5, cost=3) is False and b2.wait_time(5, cost=3) == float("inf")
    with pytest.raises(ValueError):
        TokenBucket(0, 1)
    for _ in range(200):  # property: allowed tokens never exceed capacity + rate * elapsed
        rate, cap = RNG.randint(1, 5), RNG.randint(1, 8)
        b, t, taken = TokenBucket(rate, cap, now=0), 0.0, 0
        for _ in range(50):
            t += RNG.random()
            c = RNG.randint(1, 3)
            if b.allow(t, c):
                taken += c
        assert taken <= cap + rate * t + 1e-9


def test_m12():
    ring = HashRing(["a", "b", "c"], vnodes=50)
    keys = [f"user-{i}" for i in range(2000)]
    before = {k: ring.get(k) for k in keys}
    assert before == {k: HashRing(["c", "a", "b"], vnodes=50).get(k) for k in keys}  # order independent
    ring.remove("b")
    after = {k: ring.get(k) for k in keys}
    assert all(after[k] == before[k] for k in keys if before[k] != "b")  # only b's keys move
    assert "b" not in set(after.values())
    counts = {n: sum(1 for v in before.values() if v == n) for n in "abc"}
    assert min(counts.values()) > 2000 / 3 * 0.5  # no node starves
    assert HashRing().get("x") is None
    ring.add("d")
    moved = [k for k in keys if ring.get(k) != after[k]]
    assert all(ring.get(k) == "d" for k in moved)  # keys only move to the new node


def test_m13():
    assert backoff_ceiling(0, 0.1, 30) == 0.1
    assert backoff_ceiling(3, 0.1, 30) == pytest.approx(0.8)
    assert backoff_ceiling(500, 0.1, 30) == 30  # no overflow
    a = backoff_schedule(6, 0.5, 4, random.Random(1))
    assert a == backoff_schedule(6, 0.5, 4, random.Random(1))
    assert all(0 <= d <= backoff_ceiling(i, 0.5, 4) for i, d in enumerate(a))
    assert backoff_schedule(0, 1, 2) == []
    for seed in range(50):
        s = backoff_schedule(20, 1, 8, random.Random(seed), budget=10)
        assert sum(s) <= 10


def test_m14():
    ev = [(1, "A"), (2, "B"), (4, "A"), (5, "C"), (6, "B")]
    assert shortest_span(ev, {"A", "B", "C"}) == (4, 6)
    assert shortest_span(ev, {"A", "Z"}) is None
    assert shortest_span([], {"A"}) is None
    assert shortest_span(ev, set()) is None
    assert shortest_span([(7, "A")], {"A"}) == (7, 7)
    for _ in range(400):
        t, ev = 0, []
        for _ in range(RNG.randint(0, 10)):
            t += RNG.randint(0, 3)
            ev.append((t, RNG.choice("ABCD")))
        req = set(RNG.sample("ABCD", RNG.randint(1, 3)))
        spans = [ev[j][0] - ev[i][0] for i in range(len(ev)) for j in range(i, len(ev))
                 if req <= {x[1] for x in ev[i:j + 1]}]
        got = shortest_span(ev, req)
        if not spans:
            assert got is None
        else:
            assert got[1] - got[0] == min(spans)
            assert req <= {x[1] for x in ev if got[0] <= x[0] <= got[1]}


def test_m15():
    assert decode_string("3[a2[c]]") == "accaccacc"
    assert decode_string("ab") == "ab"
    assert decode_string("") == ""
    assert decode_string("10[x]") == "x" * 10
    assert decode_string("2[a]b2[c]") == "aabcc"

    def gen(depth):
        out = ""
        for _ in range(RNG.randint(1, 3)):
            if depth and RNG.random() < 0.5:
                out += f"{RNG.randint(1, 3)}[{gen(depth - 1)}]"
            else:
                out += RNG.choice("abc")
        return out

    inner = re.compile(r"(\d+)\[([a-z]*)\]")
    for _ in range(300):
        s = gen(3)
        brute = s
        while inner.search(brute):
            brute = inner.sub(lambda m: m.group(2) * int(m.group(1)), brute)
        assert decode_string(s) == brute


def test_m16():
    kv = TimeKV()
    kv.set("k", "v1", 10)
    kv.set("k", "v2", 20)
    assert kv.get("k", 9) is None
    assert kv.get("k", 10) == "v1"
    assert kv.get("k", 19) == "v1"
    assert kv.get("k", 10**9) == "v2"
    assert kv.get("missing", 5) is None
    with pytest.raises(ValueError):
        kv.set("k", "late", 20)
    for _ in range(200):
        kv, hist, t = TimeKV(), [], 0
        for i in range(RNG.randint(0, 8)):
            t += RNG.randint(1, 3)
            kv.set("x", i, t)
            hist.append((t, i))
        for q in range(0, t + 3):
            cands = [v for ts, v in hist if ts <= q]
            assert kv.get("x", q) == (cands[-1] if cands else None)
