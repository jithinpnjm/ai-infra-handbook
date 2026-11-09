"""Tests for the four mini-projects (P1-P4)."""
import random
import threading
from datetime import datetime, timedelta, timezone

import pytest

from c11_p1_slo_burn import SloTracker, parse_line
from c11_p2_rate_limiter import BucketAdapter, KeyedLimiter, SlidingWindowLog
from c11_p3_tsdb import TimeSeriesStore
from c11_p4_rollout_planner import CycleError, blocked_by, find_cycle, plan_waves

RNG = random.Random(14)
T0 = datetime(2026, 11, 9, 10, 0, 0, tzinfo=timezone.utc)


def line(offset_s, status=200, ms=100):
    ts = (T0 + timedelta(seconds=offset_s)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"{ts} POST /v1/chat {status} {ms}"


# ---------- P1 ----------
def test_p1_parse():
    assert parse_line(line(0, 503, 50)) == (T0.timestamp(), True, 50.0)
    assert parse_line("nonsense") is None
    assert parse_line("2026-13-45T00:00:00Z GET / 200 1") is None
    assert parse_line("2026-11-09T10:00:00Z GET / abc 1") is None


def test_p1_burn_and_alert():
    tr = SloTracker(target=0.99, latency_ms=1000)
    # 100 requests in the last minute, 10 bad (5xx or slow) -> 10% bad / 1% budget = 10x
    for i in range(100):
        bad = i < 5
        tr.ingest(line(i % 50, 500 if bad else 200, 100))
    for i in range(5):
        tr.ingest(line(i, 200, 5000))
    tr.ingest("garbage")
    assert tr.malformed == 1
    now = (T0 + timedelta(seconds=59)).timestamp()
    assert tr.counts(now, 60) == (10, 105)
    assert tr.burn_rate(now, 60) == pytest.approx((10 / 105) / 0.01)
    assert tr.alerts(now, [("page", 3600, 300, 5)]) == ["page"]
    assert tr.alerts(now, [("page", 3600, 300, 50)]) == []
    assert tr.burn_rate(now + 7200, 300) == 0.0  # no traffic -> zero burn


def test_p1_short_window_recovered():
    tr = SloTracker(target=0.99)
    for i in range(300):  # 5 bad minutes, then 10 healthy minutes
        tr.ingest(line(i, 500))
    for i in range(300, 900):
        tr.ingest(line(i, 200))
    now = (T0 + timedelta(seconds=899)).timestamp()
    assert tr.burn_rate(now, 900) > 10
    assert tr.burn_rate(now, 300) == 0
    assert tr.alerts(now, [("page", 900, 300, 10)]) == []  # short window says it is over


def test_p1_memory_bounded_and_out_of_order():
    tr = SloTracker(retention_s=600)
    for i in range(0, 100_000, 7):
        tr.ingest(line(i))
    assert len(tr._buckets) <= 11
    tr2 = SloTracker()
    tr2.ingest(line(100))
    tr2.ingest(line(10))  # late line lands in its own bucket
    assert tr2.counts((T0 + timedelta(seconds=100)).timestamp(), 300) == (0, 2)


def test_p1_matches_brute_force():
    for _ in range(100):
        lines = [line(RNG.randint(0, 1800), RNG.choice([200, 200, 500, 503]), RNG.choice([50, 5000]))
                 for _ in range(RNG.randint(0, 60))]
        tr = SloTracker(target=0.95, latency_ms=1000, bucket_s=60, retention_s=10**6)
        tr.ingest_all(lines)
        now = (T0 + timedelta(seconds=RNG.randint(0, 2000))).timestamp()
        window = RNG.choice([60, 300, 900])
        end = int(now // 60)
        bad = total = 0
        for ln in lines:
            epoch, is5, ms = parse_line(ln)
            b = int(epoch // 60)
            if end - window // 60 < b <= end:
                total += 1
                bad += is5 or ms > 1000
        assert tr.counts(now, window) == (bad, total)
    with pytest.raises(ValueError):
        SloTracker(target=1.0)


# ---------- P2 ----------
def test_p2_sliding_window_boundaries():
    w = SlidingWindowLog(limit=2, window=10)
    assert w.check(0).allowed and w.check(1).allowed
    d = w.check(2)
    assert not d.allowed and d.retry_after == pytest.approx(8)
    assert w.check(9.99).allowed is False
    assert w.check(10).allowed  # event at 0 is exactly window old: it has left
    with pytest.raises(ValueError):
        SlidingWindowLog(0, 1)


def test_p2_sliding_window_vs_brute_and_retry_after():
    for _ in range(200):
        limit, window = RNG.randint(1, 4), RNG.randint(1, 6)
        w, accepted, t = SlidingWindowLog(limit, window), [], 0.0
        for _ in range(40):
            t += RNG.random() * 2
            d = w.check(t)
            expect = sum(1 for a in accepted if t - a < window) < limit
            assert d.allowed == expect
            if d.allowed:
                accepted.append(t)
            else:
                # waiting retry_after makes the same request pass (checked on a replay copy)
                replay = SlidingWindowLog(limit, window)
                for a in accepted:
                    replay.check(a)
                assert replay.check(t + d.retry_after + 1e-9).allowed


def test_p2_token_bucket_adapter():
    b = BucketAdapter(rate=1, capacity=2)
    assert b.check(100).allowed and b.check(100).allowed
    d = b.check(100)
    assert not d.allowed and d.retry_after == pytest.approx(1.0)
    assert b.check(100 + d.retry_after + 1e-9).allowed


def test_p2_keyed_isolation_and_eviction():
    kl = KeyedLimiter(lambda: SlidingWindowLog(1, 10), max_keys=2)
    assert kl.check("a", 0).allowed and not kl.check("a", 1).allowed
    assert kl.check("b", 1).allowed  # other keys are independent
    assert kl.check("c", 2).allowed  # evicts the least recently used key (a)
    assert len(kl) == 2
    assert kl.check("a", 3).allowed  # a was forgotten: lost state is the price of bounded memory


def test_p2_threads_do_not_overspend():
    kl = KeyedLimiter(lambda: SlidingWindowLog(50, 1000))
    results = []

    def work():
        for _ in range(100):
            results.append(kl.check("k", 0.0).allowed)

    threads = [threading.Thread(target=work) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sum(results) == 50 and len(results) == 800


# ---------- P3 ----------
def test_p3_basic_range_and_overwrite():
    s = TimeSeriesStore()
    for ts, v in [(10, 1), (30, 3), (20, 2)]:  # out of order
        s.insert("cpu", ts, v)
    s.insert("cpu", 20, 22)  # overwrite
    assert s.query("cpu", 0, 100) == [(10, 1), (20, 22), (30, 3)]
    assert s.query("cpu", 10, 30) == [(10, 1), (20, 22)]  # end is exclusive
    assert s.query("cpu", 31, 40) == []
    assert s.query("nope", 0, 10) == []
    assert s.query("cpu", 20, 20) == []


def test_p3_downsample_and_retention():
    s = TimeSeriesStore()
    for ts in range(0, 60, 10):
        s.insert("m", ts, ts)  # 0,10,20,30,40,50
    assert s.downsample("m", 0, 60, 30, "avg") == [(0, 10.0), (30, 40.0)]
    assert s.downsample("m", 0, 60, 30, "max") == [(0, 20), (30, 50)]
    assert s.downsample("m", 0, 60, 30, "count") == [(0, 3), (30, 3)]
    assert s.downsample("m", 0, 60, 30, "last") == [(0, 20), (30, 50)]
    assert s.downsample("m", 5, 60, 20, "sum") == [(5, 30), (25, 70), (45, 50)]  # buckets aligned to start=5
    with pytest.raises(ValueError):
        s.downsample("m", 0, 60, 0)
    assert s.drop_before("m", 30) == 3
    assert s.query("m", 0, 100) == [(30, 30), (40, 40), (50, 50)]
    assert s.drop_before("zzz", 5) == 0


def test_p3_skips_empty_buckets():
    s = TimeSeriesStore()
    s.insert("m", 0, 1)
    s.insert("m", 95, 2)
    assert s.downsample("m", 0, 100, 10, "sum") == [(0, 1), (90, 2)]


def test_p3_matches_brute_force():
    for _ in range(200):
        s, ref = TimeSeriesStore(), {}
        for _ in range(RNG.randint(0, 40)):
            ts, v = RNG.randint(0, 50), RNG.randint(-9, 9)
            s.insert("x", ts, v)
            ref[ts] = v
        a = RNG.randint(0, 50)
        b = a + RNG.randint(0, 30)
        assert s.query("x", a, b) == sorted((t, v) for t, v in ref.items() if a <= t < b)
        step = RNG.randint(1, 12)
        got = s.downsample("x", a, b, step, "sum")
        exp = {}
        for t, v in ref.items():
            if a <= t < b:
                exp[a + (t - a) // step * step] = exp.get(a + (t - a) // step * step, 0) + v
        assert got == sorted(exp.items())


# ---------- P4 ----------
DEPS = {"gateway": ["router", "auth"], "router": ["engine"], "auth": [], "engine": ["weights"], "weights": []}


def _depth(deps):
    memo = {}

    def d(n):
        if n not in memo:
            memo[n] = 1 + max((d(x) for x in deps.get(n, [])), default=0)
        return memo[n]

    nodes = set(deps) | {x for v in deps.values() for x in v}
    return {n: d(n) for n in nodes}


def test_p4_example_and_cycle():
    assert plan_waves(DEPS) == [["auth", "weights"], ["engine"], ["router"], ["gateway"]]
    assert plan_waves({}) == []
    with pytest.raises(CycleError) as e:
        plan_waves({"a": ["b"], "b": ["c"], "c": ["a"], "d": []})
    cyc = e.value.cycle
    assert cyc[0] == cyc[-1] and set(cyc) == {"a", "b", "c"}
    assert find_cycle(DEPS) is None
    assert find_cycle({"x": ["x"]}) == ["x", "x"]


def test_p4_blocked_by():
    assert blocked_by(DEPS, {"engine"}) == {"router", "gateway"}
    assert blocked_by(DEPS, {"auth"}) == {"gateway"}
    assert blocked_by(DEPS, set()) == set()
    assert blocked_by(DEPS, {"gateway"}) == set()


def test_p4_cap_and_validity_random():
    for _ in range(300):
        names = list("abcdefgh")[: RNG.randint(1, 8)]
        deps = {n: [m for m in names[:i] if RNG.random() < 0.3] for i, n in enumerate(names)}
        depth = _depth(deps)
        waves = plan_waves(deps)
        assert len(waves) == max(depth.values())
        for i, w in enumerate(waves, 1):
            assert w == sorted(n for n, d in depth.items() if d == i)
        cap = RNG.randint(1, 3)
        capped = plan_waves(deps, max_parallel=cap)
        pos = {n: i for i, w in enumerate(capped) for n in w}
        assert sorted(pos) == sorted(names) and sum(len(w) for w in capped) == len(names)
        assert all(len(w) <= cap for w in capped)
        assert all(pos[d] < pos[n] for n, ds in deps.items() for d in ds)
        assert len(capped) >= len(waves)
        # blocked_by agrees with a brute-force transitive closure
        failed = {RNG.choice(names)}
        brute = set()
        changed = True
        while changed:
            changed = False
            for n, ds in deps.items():
                if n not in brute and n not in failed and any(d in failed or d in brute for d in ds):
                    brute.add(n)
                    changed = True
        assert blocked_by(deps, failed) == brute
