import asyncio
import random
import pytest
from c09_backoff import backoff_delay, call_with_retry, RetryableError
from c09_graph import topo_order, find_cycle, shortest_path, reachable, blast_radius
from c09_unionfind import UnionFind, failing_clusters
from c09_bsearch import first_true, min_replicas, min_timeout_ms, min_window_hours, float_search
from c09_percentiles import percentile, Reservoir, LogHistogram, average_of_p99s, true_p99
from c09_strings import rle_encode, rle_decode, tokenize, collapse_ids
from c09_concurrency import run_pipeline, Counter, hammer, fetch_all


# backoff
def test_backoff_ceiling_and_cap():
    assert backoff_delay(0, 0.1, 5, rng=lambda: 1.0) == pytest.approx(0.1)
    assert backoff_delay(3, 0.1, 5, rng=lambda: 1.0) == pytest.approx(0.8)
    assert backoff_delay(30, 0.1, 5, rng=lambda: 1.0) == 5     # capped, no overflow surprise
    assert backoff_delay(3, 0.1, 5, rng=lambda: 0.0) == 0


def test_retry_succeeds_after_failures_and_sleeps_between():
    calls, sleeps = [], []

    def fn():
        calls.append(1)
        if len(calls) < 3:
            raise RetryableError()
        return "ok"
    assert call_with_retry(fn, sleep=sleeps.append, rng=lambda: 1.0) == "ok"
    assert len(calls) == 3 and sleeps == [pytest.approx(0.1), pytest.approx(0.2)]


def test_retry_gives_up_and_does_not_retry_other_errors():
    n = []

    def always():
        n.append(1)
        raise RetryableError()
    with pytest.raises(RetryableError):
        call_with_retry(always, max_attempts=3, sleep=lambda s: None)
    assert len(n) == 3

    def bad():
        raise ValueError()
    with pytest.raises(ValueError):
        call_with_retry(bad, sleep=lambda s: None)


def test_retry_respects_deadline():
    t = [0.0]

    def fn():
        raise RetryableError()
    with pytest.raises(RetryableError):
        call_with_retry(fn, max_attempts=10, base=1, cap=100, deadline_s=1.5,
                        sleep=lambda d: t.__setitem__(0, t[0] + d), rng=lambda: 1.0, clock=lambda: t[0])
    assert t[0] < 1.5


# graph
def test_topo_order_valid_and_deterministic():
    deps = {"api": ["db", "cache"], "cache": ["net"], "db": ["net"], "net": []}
    order, stuck = topo_order(deps)
    assert stuck == [] and order == ["net", "cache", "db", "api"]
    pos = {n: i for i, n in enumerate(order)}
    assert all(pos[d] < pos[n] for n, ds in deps.items() for d in ds)


def test_topo_order_includes_nodes_only_named_as_dependencies():
    order, stuck = topo_order({"a": ["x"]})
    assert order == ["x", "a"] and stuck == []


def test_cycle_detection():
    deps = {"a": ["b"], "b": ["c"], "c": ["a"], "d": ["a"]}
    order, stuck = topo_order(deps)
    assert order == [] and stuck == ["a", "b", "c", "d"]
    cyc = find_cycle(deps)
    assert cyc[0] == cyc[-1] and set(cyc) == {"a", "b", "c"}
    assert find_cycle({"a": ["b"], "b": []}) is None
    assert find_cycle({"a": ["a"]}) == ["a", "a"]


def test_topo_random_vs_find_cycle_agree():
    rng = random.Random(4)
    for _ in range(300):
        names = list("abcdef")
        deps = {n: [m for m in names if m != n and rng.random() < 0.2] for n in names}
        _, stuck = topo_order(deps)
        assert (find_cycle(deps) is not None) == bool(stuck)


def test_shortest_path_and_reachable():
    g = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": ["e"], "x": ["y"]}
    p = shortest_path(g, "a", "e")
    assert len(p) == 4 and p[0] == "a" and p[-1] == "e"
    assert shortest_path(g, "a", "a") == ["a"]
    assert shortest_path(g, "a", "y") is None
    assert reachable(g, "a") == {"a", "b", "c", "d", "e"}


def test_bfs_matches_brute_force_distance():
    rng = random.Random(8)
    for _ in range(100):
        n = 7
        g = {i: [j for j in range(n) if j != i and rng.random() < 0.25] for i in range(n)}
        dist = {0: 0}
        for _ in range(n):                    # Bellman-Ford style relaxation as the oracle
            for u in g:
                for v in g[u]:
                    if u in dist and dist[u] + 1 < dist.get(v, 99):
                        dist[v] = dist[u] + 1
        for t in range(n):
            p = shortest_path(g, 0, t)
            assert (p is None) == (t not in dist)
            if p:
                assert len(p) - 1 == dist[t]


def test_deep_chain_does_not_blow_the_stack():
    g = {i: [i + 1] for i in range(50_000)}
    assert len(reachable(g, 0)) == 50_001


def test_blast_radius():
    deps = {"api": ["db"], "web": ["api"], "db": [], "batch": []}
    assert blast_radius(deps, "db") == {"api", "web"}


# union find
def test_union_find_vs_bruteforce_components():
    rng = random.Random(6)
    for _ in range(100):
        n = 12
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 12))]
        uf = UnionFind(range(n))
        for a, b in edges:
            uf.union(a, b)
        comp = {i: {i} for i in range(n)}
        for a, b in edges:
            merged = comp[a] | comp[b]
            for x in merged:
                comp[x] = merged
        assert uf.components == len({frozenset(s) for s in comp.values()})
        assert all(uf.find(a) == uf.find(b) for a, b in edges)


def test_failing_clusters():
    links = [("n1", "n2"), ("n2", "n3"), ("n3", "n4"), ("n7", "n8")]
    assert failing_clusters(["n1", "n2", "n4", "n7", "n9"], links) == [["n1", "n2"], ["n4"], ["n7"], ["n9"]]
    assert failing_clusters([], links) == []


# binary search
def test_first_true_edges():
    assert first_true(0, 10, lambda x: x >= 4) == 4
    assert first_true(0, 10, lambda x: True) == 0
    assert first_true(0, 10, lambda x: False) == 11
    assert first_true(5, 4, lambda x: True) == 5


def test_min_replicas_vs_linear_scan():
    cap = lambda n: 100 - 0.5 * n
    for peak in (50, 1000, 4000, 9000):
        got = min_replicas(peak, cap, max_replicas=200)
        want = next((n for n in range(1, 201) if n * cap(n) >= peak), None)
        assert got == want


def test_min_timeout():
    lat = [10, 20, 30, 40, 1000]
    assert min_timeout_ms(lat, 0.8) == 40
    assert min_timeout_ms(lat, 1.0) == 1000


def test_min_window_hours_vs_bruteforce():
    rng = random.Random(10)
    for _ in range(100):
        jobs = [rng.randint(1, 9) for _ in range(rng.randint(1, 8))]
        k = rng.randint(1, 4)

        def groups(cap):
            g, load = 1, 0
            for j in jobs:
                if load + j > cap:
                    g, load = g + 1, 0
                load += j
            return g
        want = next(c for c in range(max(jobs), sum(jobs) + 1) if groups(c) <= k)
        assert min_window_hours(jobs, k) == want


def test_float_search():
    assert float_search(0, 100, lambda x: x * x >= 2) == pytest.approx(2 ** 0.5)


# percentiles
def test_percentile_nearest_rank():
    v = list(range(1, 101))
    assert percentile(v, 50) == 50 and percentile(v, 99) == 99 and percentile(v, 100) == 100
    assert percentile([7], 99) == 7
    with pytest.raises(ValueError):
        percentile([], 50)
    with pytest.raises(ValueError):
        percentile(v, 0)


def test_reservoir_is_uniform():
    hits = [0] * 20
    for seed in range(2000):
        r = Reservoir(5, random.Random(seed))
        for x in range(20):
            r.add(x)
        for x in r.items:
            hits[x] += 1
    expected = 2000 * 5 / 20
    assert all(abs(h - expected) < 0.2 * expected for h in hits)


def test_reservoir_small_stream_keeps_everything():
    r = Reservoir(10, random.Random(0))
    for x in range(4):
        r.add(x)
    assert sorted(r.items) == [0, 1, 2, 3]


def test_histogram_error_is_bounded_and_merges():
    rng = random.Random(12)
    data = [rng.lognormvariate(4, 1) for _ in range(20000)]
    a, b = LogHistogram(), LogHistogram()
    for i, x in enumerate(data):
        (a if i % 2 else b).add(x)
    a.merge(b)
    exact = percentile(sorted(data), 99)
    approx = a.quantile(0.99)
    assert exact <= approx <= exact * 1.1 * 1.001


def test_average_of_p99_is_not_the_fleet_p99():
    quiet = [10.0] * 990 + [12.0] * 10          # 1000 requests, p99 = 10
    busy = [100.0] * 10                          # 10 requests, p99 = 100
    avg = average_of_p99s([quiet, busy])
    assert avg == pytest.approx(55.0)
    assert true_p99([quiet, busy]) == 12.0


# strings
def test_rle_roundtrip_and_edges():
    assert rle_encode("aaabccdddd") == "3a1b2c4d"
    assert rle_encode("") == ""
    assert rle_decode("3a1b2c4d") == "aaabccdddd"
    assert rle_decode(rle_encode("x" * 25)) == "x" * 25      # multi-digit counts
    for bad in ("a", "3", "2a3"):
        with pytest.raises(ValueError):
            rle_decode(bad)
    rng = random.Random(1)
    for _ in range(200):
        s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 30)))
        assert rle_decode(rle_encode(s)) == s


def test_tokenize():
    assert tokenize('level=info msg="hello world" code=200') == {"level": "info", "msg": "hello world", "code": "200"}
    assert tokenize('msg="say \\"hi\\"" x=1') == {"msg": 'say "hi"', "x": "1"}
    assert tokenize("flag k=") == {"flag": "", "k": ""}
    assert tokenize("   ") == {}
    with pytest.raises(ValueError):
        tokenize('msg="open')


def test_collapse_ids():
    assert collapse_ids("/users/123/jobs/9f2c4a1b88") == "/users/:n/jobs/:hex"
    assert collapse_ids("/v1/chat") == "/v1/chat"


# concurrency
def test_pipeline_processes_everything_once():
    out = run_pipeline(range(200), 4, lambda x: x * 2)
    assert sorted(out) == [x * 2 for x in range(200)]
    assert run_pipeline([], 3, lambda x: x) == []


def test_locked_counter_is_exact():
    assert hammer(Counter(), threads=8, per_thread=5000) == 40000


def test_fetch_all_mixed_outcomes():
    async def fast():
        return 1

    async def slow():
        await asyncio.sleep(1)

    async def boom():
        raise KeyError("x")
    res = asyncio.run(fetch_all([fast, slow, boom], 0.05, 1.0))
    assert res == [("ok", 1), ("err", "timeout"), ("err", "KeyError")]


def test_fetch_all_overall_timeout_cancels_everything():
    async def slow():
        await asyncio.sleep(1)
    res = asyncio.run(fetch_all([slow, slow], 5.0, 0.05))
    assert res == [("err", "overall_timeout")] * 2
