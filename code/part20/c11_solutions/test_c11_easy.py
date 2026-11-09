"""Tests for the twelve easy problems (E1-E12)."""
import random

import pytest

from c11_e01_first_unique import first_unique
from c11_e02_compress_string import compress, decompress
from c11_e03_status_classes import status_class_counts
from c11_e04_balanced_brackets import balanced
from c11_e05_merge_sorted import merge_sorted
from c11_e06_top_k_errors import top_k_errors
from c11_e07_pair_sum import pair_sum
from c11_e08_longest_ok_streak import longest_ok_streak
from c11_e09_percentile import percentile
from c11_e10_moving_average import moving_average
from c11_e11_missing_shard import missing_shard
from c11_e12_duplicate_within_k import duplicate_within_k

RNG = random.Random(11)


def test_e01():
    assert first_unique(["a", "b", "a", "c", "b"]) == "c"
    assert first_unique([]) is None
    assert first_unique([1, 1]) is None
    for _ in range(300):
        xs = [RNG.randint(0, 6) for _ in range(RNG.randint(0, 12))]
        brute = next((x for x in xs if xs.count(x) == 1), None)
        assert first_unique(xs) == brute


def test_e02():
    assert compress("aaabcc") == "a3bc2"
    assert compress("abc") == "abc"
    assert compress("aabb") == "aabb"  # 'a2b2' is the same length: keep original
    assert compress("") == ""
    assert compress("a") == "a"
    assert compress("a" * 12) == "a12"
    assert decompress("a12b") == "a" * 12 + "b"
    for _ in range(300):
        s = "".join(RNG.choice("abc") * RNG.randint(1, 5) for _ in range(RNG.randint(0, 8)))
        packed = compress(s)
        assert len(packed) <= len(s)
        assert packed == s or decompress(packed) == s


def test_e03():
    lines = [
        "2026-11-09T10:00:00Z GET /v1/chat 200 12ms",
        "2026-11-09T10:00:01Z POST /v1/chat 503 900ms",
        "2026-11-09T10:00:02Z POST /v1/chat 429 3ms",
        "garbage",
        "2026-11-09T10:00:02Z POST /v1/chat 99 3ms",
        "2026-11-09T10:00:02Z POST /v1/chat 700 3ms",
    ]
    c = status_class_counts(lines)
    assert c["2xx"] == 1 and c["5xx"] == 1 and c["4xx"] == 1
    assert c["malformed"] == 2 and c["other"] == 1
    assert status_class_counts([])["malformed"] == 0


@pytest.mark.parametrize("s,ok", [
    ("", True), ("()", True), ("([]{})", True), ("(]", False), ("(()", False),
    ("())", False), ("a(b)c", True), ("{[}]", False), ("]", False),
])
def test_e04(s, ok):
    assert balanced(s) is ok


def test_e05():
    assert merge_sorted([1, 3, 5], [2, 3, 6]) == [1, 2, 3, 3, 5, 6]
    assert merge_sorted([], [1]) == [1]
    assert merge_sorted([], []) == []
    for _ in range(300):
        a = sorted(RNG.randint(0, 9) for _ in range(RNG.randint(0, 8)))
        b = sorted(RNG.randint(0, 9) for _ in range(RNG.randint(0, 8)))
        assert merge_sorted(a, b) == sorted(a + b)


def test_e06():
    msgs = ["oom", "timeout", "oom", "reset", "timeout", "oom", "reset"]
    assert top_k_errors(msgs, 2) == [("oom", 3), ("reset", 2)]
    assert top_k_errors(msgs, 0) == []
    assert top_k_errors([], 3) == []
    assert top_k_errors(msgs, 10) == [("oom", 3), ("reset", 2), ("timeout", 2)]


def test_e07():
    assert pair_sum([4, 9, 1, 6], 10) == (1, 2)
    assert pair_sum([5, 5], 10) == (0, 1)
    assert pair_sum([5], 10) is None
    assert pair_sum([], 1) is None
    for _ in range(400):
        xs = [RNG.randint(-3, 6) for _ in range(RNG.randint(0, 8))]
        b = RNG.randint(-2, 10)
        brute = next(((i, j) for j in range(len(xs)) for i in range(j) if xs[i] + xs[j] == b), None)
        assert pair_sum(xs, b) == brute


def test_e08():
    assert longest_ok_streak([200, 200, 500, 404, 200, 200, 200, 503]) == 4
    assert longest_ok_streak([]) == 0
    assert longest_ok_streak([500, 502]) == 0
    assert longest_ok_streak([200] * 5) == 5


def test_e09():
    xs = list(range(1, 11))
    assert percentile(xs, 50) == 5
    assert percentile(xs, 90) == 9
    assert percentile(xs, 100) == 10
    assert percentile([7], 1) == 7
    assert percentile(list(range(1, 1001)), 99.9) == 999
    with pytest.raises(ValueError):
        percentile([], 50)
    with pytest.raises(ValueError):
        percentile(xs, 0)


def test_e10():
    assert moving_average([1, 2, 3, 4, 5], 2) == [1.5, 2.5, 3.5, 4.5]
    assert moving_average([1, 2], 3) == []
    assert moving_average([4], 1) == [4.0]
    with pytest.raises(ValueError):
        moving_average([1], 0)
    for _ in range(200):
        xs = [RNG.randint(-9, 9) for _ in range(RNG.randint(0, 12))]
        k = RNG.randint(1, 5)
        brute = [sum(xs[i:i + k]) / k for i in range(len(xs) - k + 1)]
        assert moving_average(xs, k) == pytest.approx(brute)


def test_e11():
    assert missing_shard([0, 1, 3], 3) == 2
    assert missing_shard([], 0) == 0
    assert missing_shard([1], 1) == 0
    for _ in range(100):
        n = RNG.randint(1, 20)
        full = list(range(n + 1))
        gone = RNG.choice(full)
        full.remove(gone)
        RNG.shuffle(full)
        assert missing_shard(full, n) == gone


def test_e12():
    assert duplicate_within_k([1, 2, 1], 2) is True
    assert duplicate_within_k([1, 2, 1], 1) is False
    assert duplicate_within_k([1, 1], 0) is False
    assert duplicate_within_k([], 3) is False
    for _ in range(400):
        xs = [RNG.randint(0, 5) for _ in range(RNG.randint(0, 10))]
        k = RNG.randint(0, 6)
        brute = any(xs[i] == xs[j] for i in range(len(xs)) for j in range(i + 1, min(len(xs), i + k + 1)))
        assert duplicate_within_k(xs, k) is brute
