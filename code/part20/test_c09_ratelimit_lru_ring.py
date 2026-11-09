import random
from collections import OrderedDict
from c09_ratelimit import FixedWindow, SlidingLog, SlidingCounter, TokenBucket, LeakyBucket
from c09_lru import LRUOrdered, LRUList
from c09_hashring import Ring, balance, moved_fraction, modulo_moved_fraction, h


def count(limiter, times):
    return sum(limiter.allow(t) for t in times)


def test_fixed_window_edge_burst_is_double():
    f = FixedWindow(10, 1.0)
    burst = [0.99] * 10 + [1.0] * 10          # 20 requests inside 10 ms
    assert count(f, burst) == 20


def test_sliding_log_is_exact_at_the_edge():
    s = SlidingLog(10, 1.0)
    burst = [0.99] * 10 + [1.0] * 10
    assert count(s, burst) == 10
    assert s.allow(1.99) is True              # the 0.99 entries are now exactly 1.0 s old


def test_sliding_counter_bounds_the_edge_burst():
    s = SlidingCounter(10, 1.0)
    burst = [0.99] * 10 + [1.0] * 10
    assert count(s, burst) <= 11


def test_sliding_counter_idle_gap_resets():
    s = SlidingCounter(2, 1.0)
    assert s.allow(0.1) and s.allow(0.2) and not s.allow(0.3)
    assert s.allow(10.0)


def test_token_bucket_burst_then_rate():
    b = TokenBucket(rate=5, burst=10)
    assert count(b, [0.0] * 12) == 10         # burst of 10, then empty
    assert b.allow(0.2) is True               # 0.2 s * 5/s = 1 token
    assert b.allow(0.2) is False


def test_token_bucket_never_exceeds_burst_after_idle():
    b = TokenBucket(rate=5, burst=10)
    b.allow(0.0)
    assert count(b, [1000.0] * 15) == 10


def test_token_bucket_long_run_rate():
    b = TokenBucket(rate=5, burst=10)
    allowed = sum(b.allow(t / 100) for t in range(0, 6000))   # 100 req/s offered for 60 s
    assert 5 * 60 <= allowed <= 5 * 60 + 10


def test_leaky_bucket_smooths_burst():
    b = LeakyBucket(rate=5, capacity=3)
    assert count(b, [0.0] * 10) == 3
    assert b.allow(1.0) is True


def test_lru_both_agree_with_each_other_and_a_model():
    rng = random.Random(11)
    for cap in (1, 2, 5):
        a, b = LRUOrdered(cap), LRUList(cap)
        model = OrderedDict()
        for _ in range(2000):
            k = rng.randint(0, 8)
            if rng.random() < 0.5:
                assert a.get(k) == b.get(k) == (model[k] if k in model else None)
                if k in model:
                    model.move_to_end(k)
            else:
                v = rng.random()
                a.put(k, v); b.put(k, v)
                model[k] = v
                model.move_to_end(k)
                if len(model) > cap:
                    model.popitem(last=False)
            assert a.keys_oldest_first() == b.keys_oldest_first() == list(model)


def test_lru_get_refreshes_and_put_updates():
    c = LRUList(2)
    c.put("a", 1); c.put("b", 2)
    c.get("a")
    c.put("c", 3)                              # evicts b, not a
    assert c.get("b") is None and c.get("a") == 1
    c.put("a", 9)
    assert c.get("a") == 9 and len(c.map) == 2


def test_lru_zero_value_is_a_hit():
    c = LRUOrdered(2)
    c.put("x", 0)
    assert c.get("x", "miss") == 0


def test_ring_lookup_is_stable_and_wraps():
    r = Ring(["a", "b", "c"], vnodes=50)
    assert all(r.lookup(f"k{i}") == r.lookup(f"k{i}") for i in range(100))
    assert r.lookup("k1") in {"a", "b", "c"}
    assert h("x") == h("x")


def test_ring_balance_improves_with_vnodes():
    keys = [f"user-{i}" for i in range(20000)]
    nodes = [f"n{i}" for i in range(10)]
    few, _ = balance(Ring(nodes, vnodes=1), keys)
    many, _ = balance(Ring(nodes, vnodes=200), keys)
    assert many < few and many < 1.3


def test_ring_adding_a_node_moves_about_one_over_n():
    keys = [f"user-{i}" for i in range(20000)]
    nodes = [f"n{i}" for i in range(10)]
    before = Ring(nodes, vnodes=200)
    after = Ring(nodes + ["n10"], vnodes=200)
    ring_moved = moved_fraction(before, after, keys)
    mod_moved = modulo_moved_fraction(10, 11, keys)
    assert 0.05 < ring_moved < 0.15           # about 1/11
    assert mod_moved > 0.85                   # modulo hashing reshuffles almost everything


def test_ring_remove_only_moves_removed_nodes_keys():
    keys = [f"user-{i}" for i in range(5000)]
    r = Ring(["a", "b", "c"], vnodes=50)
    owners = {k: r.lookup(k) for k in keys}
    r.remove("b")
    for k in keys:
        if owners[k] != "b":
            assert r.lookup(k) == owners[k]
        else:
            assert r.lookup(k) in {"a", "c"}
