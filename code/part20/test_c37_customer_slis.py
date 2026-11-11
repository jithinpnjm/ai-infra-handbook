import pytest

import c37_customer_slis as c


def test_availability_and_burn():
    a = c.availability_sli(c.synthetic_samples())
    # 10 min of 300 5xx out of 1200, plus 429 that are not counted bad
    assert a == pytest.approx(1 - 3000 / 72000)
    assert c.burn_rate(a, 0.999) == pytest.approx((3000 / 72000) / 0.001)


def test_429_policy_changes_result():
    s = c.synthetic_samples()
    strict = c.availability_sli(s, count_429_as_bad=True)
    assert strict < c.availability_sli(s)


def test_client_4xx_leave_denominator():
    s = [c.Sample(0, 100, {"400": 50, "500": 5}, 0, 0, 0, 0)]
    assert c.availability_sli(s) == pytest.approx(45 / 50)


def test_bounds_from_percentiles():
    assert c.fraction_below_bounds(0.3, 0.8, 1.4, 2.0) == (0.99, 1.0)
    assert c.fraction_below_bounds(0.3, 0.8, 1.4, 1.0) == (0.90, 0.99)
    assert c.fraction_below_bounds(0.3, 0.8, 1.4, 0.1) == (0.0, 0.5)


def test_ttft_verdict_can_be_indeterminate():
    lo, hi = c.ttft_sli_bounds(c.synthetic_samples(), 1.0)
    assert lo < hi
    assert c.verdict(lo, hi, 0.99) == "missed"
    assert c.verdict(0.95, 1.0, 0.99) == "indeterminate"
    assert c.verdict(0.995, 1.0, 0.99) == "met"


def test_capacity_flags():
    s = [c.Sample(0, 10, {}, 0, 0, 0, 0, 4, 0.9, 0.95),
         c.Sample(1, 10, {}, 0, 0, 0, 0, 2, 0.4, 0.8)]
    assert [f[1] for f in c.capacity_flags(s, 4)] == [
        "at ceiling and hot", "one replica far busier than average"]


def test_failures():
    with pytest.raises(c.SliInputError):
        c.availability_sli([])
    with pytest.raises(c.SliInputError):
        c.availability_sli([c.Sample(0, 10, {"500": 11})])
    with pytest.raises(c.SliInputError):
        c.availability_sli([c.Sample(1, 10), c.Sample(1, 10)])
    with pytest.raises(c.SliInputError):
        c.ttft_sli_bounds([c.Sample(0, 10, {}, 5, 2.0, 1.0, 3.0)], 1.0)
    with pytest.raises(c.SliInputError):
        c.ttft_sli_bounds([c.Sample(0, 10)], 1.0)
    with pytest.raises(c.SliInputError):
        c.burn_rate(0.9, 1.0)
