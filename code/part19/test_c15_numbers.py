import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import c15_numbers as n  # noqa: E402
import c15_sheet_validator as val  # noqa: E402


def test_link_rate():
    assert n.gbps_to_gb_per_s(400) == 50


def test_6nd_example():
    assert n.train_flops(70e9, 100e9) == pytest.approx(4.2e22)
    assert n.train_days(70e9, 100e9, 128, 989, 0.40) == pytest.approx(9.6, abs=0.05)


def test_mfu_example():
    assert n.mfu(430, 989) == pytest.approx(0.4348, abs=1e-4)


def test_kv_bytes():
    assert n.kv_bytes_per_token(32, 8, 128) == 131072
    assert n.kv_bytes_per_token(36, 8, 128) == 147456
    assert 2500 * 147456 / 1e9 == pytest.approx(0.36864)


def test_decode_ceiling_and_latency():
    assert round(n.decode_ceiling_tokens_per_s(3350, 16.4)) == 204
    assert n.e2e_latency(0.4, 0.04, 500) == pytest.approx(20.36)


def test_burn_table():
    assert n.burn_rate(0.01, 0.999) == pytest.approx(10)
    assert n.hours_to_empty(720, 10) == 72
    assert n.budget_minutes(0.999, 30) == pytest.approx(43.2)
    assert n.budget_used(14.4, 1) == pytest.approx(0.02)
    assert n.budget_used(6, 6) == pytest.approx(0.05)
    assert n.budget_used(1, 72) == pytest.approx(0.10)


def test_busbw_and_bisection():
    assert n.busbw_from_algbw(24.0, 16) == pytest.approx(45.0)
    assert (n.bisect_rounds(8), n.bisect_rounds(128)) == (3, 7)


def test_checkpoint_rows_match_chapter_19_4():
    sync = n.checkpoint_row(16384, 22.5)
    asyn = n.checkpoint_row(16384, 2.0)
    assert sync["mtbf_h"] == pytest.approx(3.09, abs=0.01)
    assert round(sync["daly_s"]) == 685 and round(sync["waste"] * 100, 2) == 11.47
    assert round(asyn["daly_s"]) == 209 and round(asyn["waste"] * 100, 2) == 7.22


def test_sheet_rows_quote_the_computed_figures():
    text = open(val.DEFAULT_SHEET, encoding="utf-8").read()
    for needle in ("131,072", "147,456", "204", "20.36", "9.6 days", "43.48", "685 s", "11.47", "209 s", "7.22"):
        assert needle in text, needle
