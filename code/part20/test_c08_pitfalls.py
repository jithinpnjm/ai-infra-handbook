import c08_pitfalls as p


def test_mutable_default_is_shared():
    first = p.append_bad(1)
    second = p.append_bad(2)
    assert first is second and second[-2:] == [1, 2]
    assert p.append_good(1) == [1] and p.append_good(2) == [2]


def test_division():
    assert p.division_demo() == (3.5, 3, -4, 2)


def test_grids():
    assert p.aliased_grid() == [[1, 0], [1, 0]]
    assert p.real_grid() == [[1, 0], [0, 0]]


def test_slice_copies():
    assert p.slice_is_a_copy() == ([0, 1, 2, 3, 4], [99, 2, 3])


def test_recursion():
    assert p.default_recursion_limit() == 1000
    assert p.recursion_fails_at(5000) is True
    assert p.depth(100) == 100


def test_floats_stability_order_mutation():
    assert p.float_traps() == (False, True)
    assert p.sort_is_stable() == [("c", 0), ("b", 1), ("a", 1)]
    assert p.dict_keeps_insertion_order() == (["z", "a"], True)
    assert p.mutate_while_iterating() == [4, 8]
    assert p.groupby_without_sorting() == [("a", 2), ("b", 1), ("a", 2)]
