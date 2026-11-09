"""Only relationships that must hold. No absolute times are asserted."""
import c10_complexity_bench as b
import c10_locality as loc
import c10_loop_budget as lb
import c10_profile_demo as pd


def test_set_lookup_beats_list_scan_for_large_n():
    t_list, t_set = b.membership(50_000, probes=50)
    assert t_set * 5 < t_list


def test_list_scan_cost_grows_with_n():
    small, _ = b.membership(2_000, probes=50)
    large, _ = b.membership(100_000, probes=50)
    assert large > 5 * small


def test_deque_front_insert_beats_list_for_large_n():
    t_list, t_deque = b.front_insert(100_000, ops=500)
    assert t_deque * 5 < t_list


def test_join_beats_concat_when_string_is_shared():
    shared = b.concat_shared(20_000)
    _, t_join = b.concat(20_000)
    assert t_join < shared


def test_shared_concat_is_superlinear():
    t1 = b.concat_shared(10_000)
    t4 = b.concat_shared(40_000)
    assert t4 > 5 * t1  # four times the data costs far more than four times


def test_sorted_input_sorts_faster_than_random():
    random_t, sorted_t = b.sort_cost(200_000)
    assert sorted_t < random_t


def test_list_capacity_grows_in_jumps_not_every_append():
    points = b.growth_points(200)
    assert 0 < len(points) < 60       # far fewer reallocations than appends
    assert [s for _, s in points] == sorted(s for _, s in points)


def test_builtin_sum_beats_python_loop():
    n = 300_000
    assert lb.ns_per_item(lb.builtin_sum, n) < lb.ns_per_item(lb.plain_loop, n)


def test_loop_functions_agree():
    assert lb.plain_loop(1000) == lb.builtin_sum(1000) == 499500
    assert lb.with_call(10) == 55


def test_locality_functions_agree():
    data, order = loc.make(1000)
    assert loc.sum_in_order(data, order) == loc.sum_shuffled(data, order)


def test_profile_slow_and_fast_agree_and_report_names_the_hot_function():
    data = [i % 300 for i in range(2000)]
    assert pd.dedupe_slow(data) == pd.dedupe_fast(data)
    assert "dedupe_slow" in pd.profile_text(pd.dedupe_slow, data)
