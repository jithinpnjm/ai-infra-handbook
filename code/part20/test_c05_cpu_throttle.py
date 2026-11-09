import pytest
from c05_cpu_throttle import parse_cpu_stat, cpu_limit, burst_throttle_ms, report

# Systems Performance 2nd ed, chapter 11: cgroup v1 sample, 74 of 507 periods, 3.8 s.
V1 = "nr_periods 507\nnr_throttled 74\nthrottled_time 3816445175\n"
# cgroup v2 shape from the kernel docs, values made up for the test.
V2 = ("usage_usec 100\nuser_usec 60\nsystem_usec 40\n"
      "nr_periods 10\nnr_throttled 4\nthrottled_usec 2500000\nnr_bursts 0\nburst_usec 0\n")


def test_v1_converts_nanoseconds():
    stat = parse_cpu_stat(V1)
    assert stat["nr_throttled"] == 74
    assert stat["throttled_usec"] == 3816445


def test_v2_reads_usec():
    assert parse_cpu_stat(V2)["throttled_usec"] == 2500000


def test_missing_keys_raise():
    with pytest.raises(ValueError):
        parse_cpu_stat("usage_usec 1\nuser_usec 1\nsystem_usec 0\n")


def test_cpu_limit_values():
    assert cpu_limit("max 100000") is None
    assert cpu_limit("50000 100000") == 0.5
    assert cpu_limit("300000 100000") == 3.0


def test_book_multithread_example_throttles_80ms():
    assert burst_throttle_ms(1, 5) == pytest.approx(80.0)


def test_single_thread_under_limit_never_throttles():
    assert burst_throttle_ms(1, 1) == 0.0
    assert burst_throttle_ms(2, 1) == 0.0


def test_report_ratio_from_book_numbers():
    zero = {"nr_periods": 0, "nr_throttled": 0, "throttled_usec": 0}
    result = report(zero, parse_cpu_stat(V1))
    assert result["throttle_ratio"] == pytest.approx(74 / 507)
    assert result["throttled_seconds"] == pytest.approx(3.816445)


def test_report_no_periods():
    same = {"nr_periods": 5, "nr_throttled": 0, "throttled_usec": 0}
    assert report(same, same)["throttle_ratio"] == 0.0
