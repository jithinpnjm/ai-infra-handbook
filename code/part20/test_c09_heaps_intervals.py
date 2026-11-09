import heapq
import random
from c09_heaps import top_k_slowest, merge_k_sorted, RunningMedian
from c09_intervals import merge_intervals, free_slots, min_gpu_nodes, max_overlap_sweep, fits_window


def test_top_k_matches_sort():
    rng = random.Random(3)
    for _ in range(100):
        data = [(f"/e{rng.randint(0, 9)}", rng.randint(1, 50)) for _ in range(rng.randint(0, 40))]
        k = rng.randint(0, 8)
        want = sorted(((e, m) for e, m in data), key=lambda x: (x[1], x[0]), reverse=True)[:k]
        assert top_k_slowest(data, k) == want


def test_top_k_edges():
    assert top_k_slowest([], 3) == []
    assert top_k_slowest([("a", 1)], 0) == []
    assert top_k_slowest([("a", 1), ("b", 2)], 5) == [("b", 2), ("a", 1)]


def test_merge_k_sorted():
    rng = random.Random(5)
    for _ in range(100):
        streams = [sorted(rng.randint(0, 30) for _ in range(rng.randint(0, 6))) for _ in range(rng.randint(0, 5))]
        assert list(merge_k_sorted(streams)) == list(heapq.merge(*streams))
    assert list(merge_k_sorted([])) == []
    assert list(merge_k_sorted([[], []])) == []


def test_merge_k_is_lazy():
    def endless():
        i = 0
        while True:
            yield i
            i += 2
    g = merge_k_sorted([endless(), iter([1, 3])])
    assert [next(g) for _ in range(5)] == [0, 1, 2, 3, 4]


def test_running_median():
    rm = RunningMedian()
    xs = []
    rng = random.Random(2)
    for _ in range(100):
        x = rng.randint(0, 50)
        xs.append(x)
        rm.add(x)
        s = sorted(xs)
        n = len(s)
        want = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        assert rm.median() == want


def test_merge_intervals():
    assert merge_intervals([(5, 6), (1, 3), (2, 4)]) == [(1, 4), (5, 6)]
    assert merge_intervals([(1, 10), (2, 3)]) == [(1, 10)]    # contained interval must not shrink
    assert merge_intervals([(1, 2), (2, 3)]) == [(1, 3)]      # touching intervals merge
    assert merge_intervals([]) == []


def test_free_slots():
    assert free_slots([(2, 4), (3, 5), (8, 9)], 0, 10) == [(0, 2), (5, 8), (9, 10)]
    assert free_slots([], 0, 5) == [(0, 5)]
    assert free_slots([(0, 10)], 0, 10) == []
    assert free_slots([(-5, 2), (9, 20)], 0, 10) == [(2, 9)]


def test_min_nodes_matches_sweep_and_brute():
    rng = random.Random(9)
    for _ in range(300):
        res = []
        for _ in range(rng.randint(0, 8)):
            s = rng.randint(0, 15)
            res.append((s, s + rng.randint(1, 6)))
        brute = max((sum(s <= t < e for s, e in res) for t in range(0, 25)), default=0)
        assert min_gpu_nodes(res) == max_overlap_sweep(res) == brute


def test_back_to_back_reservations_share_a_node():
    assert min_gpu_nodes([(0, 10), (10, 20)]) == 1


def test_fits_window():
    assert fits_window([(0, 5)], (5, 8))
    assert not fits_window([(0, 5)], (4, 8))
