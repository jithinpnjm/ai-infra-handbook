import pytest
from c32_token_economics import (Segment, billed_minutes, breakeven_tokens_per_month,
                                 cache_saving_fraction, dedicated_cost, next_scale, ramp,
                                 request_cost, windows_to_reach)

P = (1.00, 0.10, 3.00)  # placeholder prices per million tokens


def test_docs_example_split():
    # 3,108 prompt tokens, 3,072 cached: 36 input + 3,072 cached + 62 output
    expected = (36 * 1.00 + 3072 * 0.10 + 62 * 3.00) / 1e6
    assert request_cost(3108, 3072, 62, *P) == pytest.approx(expected)
    assert expected == pytest.approx(0.0005292)


def test_no_cache_hit_bills_everything_at_input_price():
    assert request_cost(1000, 0, 0, *P) == pytest.approx(0.001)


def test_cached_cannot_exceed_prompt():
    with pytest.raises(ValueError):
        request_cost(100, 101, 0, *P)


def test_saving_fraction():
    assert cache_saving_fraction(3108, 3072, 62, *P) == pytest.approx(0.8394, abs=1e-3)
    assert cache_saving_fraction(100, 0, 10, *P) == 0.0


def test_dedicated_cost_per_minute():
    assert dedicated_cost(2.0, 8, 30) == pytest.approx(8.0)
    assert dedicated_cost(2.0, 1, 60, replicas=3) == pytest.approx(6.0)


def test_breakeven():
    assert breakeven_tokens_per_month(1000, 2.0) == pytest.approx(500e6)


def test_billing_readings_disagree_on_partial_readiness():
    segs = [Segment(10, "not_ready", 0), Segment(20, "partially_ready", 1),
            Segment(30, "ready", 2)]
    assert billed_minutes(segs, "table") == 30
    assert billed_minutes(segs, "prose") == 50
    with pytest.raises(ValueError):
        billed_minutes(segs, "other")


def test_ramp_matches_docs_table():
    r = ramp(8)
    assert [round(r[i], 2) for i in (0, 1, 2, 4, 8)] == [1.0, 1.2, 1.44, 2.07, 4.30]
    # docs table: 60 RPM and 400,000 TPM baseline, shown rounded
    assert [round(60 * r[i]) for i in (1, 2, 4, 8)] == [72, 86, 124, 258]
    assert round(400_000 * r[8], -4) == 1_720_000


def test_scale_down_and_hold():
    assert next_scale(3.0, 0.5) == pytest.approx(2.0)
    assert next_scale(3.0, 0.65) == 3.0
    assert next_scale(1.0, 0.1) == 1.0  # never below the base allocation


def test_ceiling_is_20x():
    assert ramp(40)[-1] == 20.0
    assert windows_to_reach(20) == 17  # 1.2**16 = 18.5, 1.2**17 = 22.2
    assert windows_to_reach(1) == 0
