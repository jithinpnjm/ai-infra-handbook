import c08_stdlib_tour as t


def test_counter():
    common, missing, added = t.counter_demo()
    assert common == [("a", 5), ("b", 2)] and missing == 0
    assert added == {"b": 2, "a": 1, "c": 1}


def test_defaultdict_read_creates_key():
    assert t.defaultdict_demo() == {"x": [1], "missing": []}


def test_deque_maxlen():
    assert t.deque_demo() == [0, 2, 3]


def test_heap_and_bisect():
    assert t.heap_demo() == (1, [9, 5], 5)
    assert t.bisect_demo() == (1, 4, 4)


def test_itertools():
    acc, pairs, first3, n, groups = t.itertools_demo()
    assert acc == [1, 3, 6, 10] and pairs[0] == ("a", "b") and first3 == [0, 1, 2]
    assert n == 8 and groups == [("a", 2), ("b", 3), ("c", 1)]


def test_cache_dataclass_regex_statistics():
    assert t.cache_info_demo() == (832040, 31)
    assert t.dataclass_demo() == ("a", True)
    assert t.regex_demo() == ("10.0.0.7", "503", 12, ["1", "22", "333"])
    assert t.statistics_demo() == (22, 3, 2.5, [1.5, 3.0, 52.0])
