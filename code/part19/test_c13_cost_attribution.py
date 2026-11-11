"""Tests for the chapter 19.13 cost attribution: conservation, both idle rules and failure cases."""
import copy
from decimal import Decimal

import pytest

import c13_cost_attribution as c

HERE = c.HERE


@pytest.fixture
def rows():
    return c.load_usage(HERE / "c13_usage_sample.csv")


@pytest.fixture
def params():
    return c.load_params(HERE / "c13_cost_params.json")


@pytest.mark.parametrize("mode", ["pro_rata", "quota"])
def test_bills_add_up_to_pool_cost_exactly(rows, params, mode):
    res = c.attribute(rows, params, mode)
    assert sum(b["total"] for b in res["bills"].values()) == res["pool_total"]


def test_pool_total_is_capacity_plus_storage_plus_platform(rows, params):
    res = c.attribute(rows, params)
    storage = sum(r["tb"] for r in rows) * params["storage_price_per_tb_month"]
    expect = Decimal(64 * 720) * Decimal("2.50") + storage + Decimal("6000.00")
    assert res["pool_total"] == expect.quantize(Decimal("0.01"))


def test_quota_rule_charges_light_teams_more_than_pro_rata(rows, params):
    a = c.attribute(rows, params, "pro_rata")["bills"]["team-d"]["total"]
    b = c.attribute(rows, params, "quota")["bills"]["team-d"]["total"]
    assert b > a


def test_quota_rule_splits_idle_equally_for_equal_quota(rows, params):
    shares = {b["idle_share"] for b in c.attribute(rows, params, "quota")["bills"].values()}
    assert len(shares) == 1


def test_idle_held_hours_reported_but_still_charged(rows, params):
    b = c.attribute(rows, params)["bills"]["team-a"]
    assert b["idle_held_hours"] == Decimal(10410 - 8340)
    assert b["direct_gpu"] == Decimal(10410) * Decimal("2.50")


def test_split_remainder_cents_are_not_lost():
    out = c._split(Decimal("100.00"), {"a": Decimal(1), "b": Decimal(1), "c": Decimal(1)})
    assert sum(out.values()) == Decimal("100.00")


def test_showback_by_project(rows, params):
    sb = c.by_project(rows, params)
    assert sb[("team-a", "notebooks")] == Decimal("1525.00")


def test_over_capacity_rejected(rows, params):
    p = copy.deepcopy(params)
    p["hours_in_month"] = 100
    with pytest.raises(c.UsageError, match="exceeds capacity"):
        c.attribute(rows, p)


def test_unknown_team_rejected(rows, params):
    r = copy.deepcopy(rows)
    r[0]["team"] = "team-x"
    with pytest.raises(c.UsageError, match="quota share"):
        c.attribute(r, params)


def test_bad_csv_rows_rejected(tmp_path):
    f = tmp_path / "u.csv"
    f.write_text("team,project,pool,gpu_hours_allocated,gpu_hours_busy,storage_tb\nt,p,batch,10,20,1\n")
    with pytest.raises(c.UsageError, match="busy hours exceed"):
        c.load_usage(f)
    f.write_text("team,project,pool,gpu_hours_allocated,gpu_hours_busy,storage_tb\nt,p,batch,-1,0,1\n")
    with pytest.raises(c.UsageError, match="negative"):
        c.load_usage(f)


def test_unknown_idle_mode(rows, params):
    with pytest.raises(c.UsageError):
        c.attribute(rows, params, "vibes")
