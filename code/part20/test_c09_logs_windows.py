import random
import pytest
from c09_logs import parse_line, aggregate, error_rate, top_paths, first_duplicate_request_id
from c09_window import RollingErrorRate, sliding_max, sliding_max_naive, longest_run_below
from c09_pointers import two_sum_sorted, merge_sorted, dedupe_in_place, common_sorted


def test_parse_and_aggregate_with_malformed_lines():
    lines = ["1 POST /v1/chat 200 120.5", "2 POST /v1/chat 503 9", "garbage",
             "3 GET /health 200 x", "4 GET /health 200 1"]
    stats, bad = aggregate(lines)
    assert bad == 2
    assert stats["/v1/chat"]["n"] == 2 and error_rate(stats["/v1/chat"]) == 0.5
    assert parse_line("") is None


def test_top_paths_ties_are_stable():
    lines = ["1 G /b 200 1", "2 G /a 200 1", "3 G /c 200 1", "4 G /c 200 1"]
    assert top_paths(lines, 2) == [("/c", 2), ("/a", 1)]
    assert top_paths([], 3) == []


def test_first_duplicate():
    assert first_duplicate_request_id(["a", "b", "a", "b"]) == "a"
    assert first_duplicate_request_id([]) is None


def test_rolling_error_rate_window_edges():
    r = RollingErrorRate(10)
    r.add(0, True)
    r.add(5, False)
    assert r.rate(5) == 0.5
    assert r.rate(10) == 0.0        # the event at t=0 is exactly 10 s old: out of the window
    assert r.rate(100) == 0.0       # empty window: no division by zero


def test_sliding_max_matches_naive_random():
    rng = random.Random(7)
    for _ in range(200):
        vals = [rng.randint(-5, 5) for _ in range(rng.randint(1, 30))]
        k = rng.randint(1, len(vals))
        assert sliding_max(vals, k) == sliding_max_naive(vals, k)


def test_sliding_max_edges():
    assert sliding_max([], 3) == []
    assert sliding_max([5], 1) == [5]
    assert sliding_max([1, 2, 3], 5) == []
    with pytest.raises(ValueError):
        sliding_max([1], 0)


def test_longest_run_below():
    assert longest_run_below([1, 2, 3, 4], 5) == 2
    assert longest_run_below([9], 5) == 0
    assert longest_run_below([], 5) == 0


def test_two_sum_sorted_vs_bruteforce():
    rng = random.Random(1)
    for _ in range(200):
        a = sorted(rng.randint(0, 20) for _ in range(rng.randint(0, 10)))
        t = rng.randint(0, 40)
        got = two_sum_sorted(a, t)
        want = any(a[i] + a[j] == t for i in range(len(a)) for j in range(i + 1, len(a)))
        assert (got is not None) == want
        if got:
            assert a[got[0]] + a[got[1]] == t and got[0] < got[1]


def test_merge_dedupe_common():
    assert merge_sorted([1, 3, 5], [2, 3, 6]) == [1, 2, 3, 3, 5, 6]
    assert merge_sorted([], [1]) == [1]
    a = [1, 1, 2, 2, 2, 3]
    n = dedupe_in_place(a)
    assert n == 3 and a == [1, 2, 3]
    assert dedupe_in_place([]) == 0
    assert common_sorted([1, 1, 2, 4], [1, 1, 3, 4, 4]) == [1, 4]
