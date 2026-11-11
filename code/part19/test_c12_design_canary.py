import c12_design_canary as c
import c12_size_inference_pool as p

HOT = p.WORKLOADS[0]


def m(**kw):
    base = dict(requests=1000, ttft_p99_s=1.0, itl_p99_s=0.05, error_rate=0.001,
                length_share=0.05, quality=0.9, tokens_per_s=500)
    base.update(kw)
    return c.Metrics(**base)


NB = {"docsum": 2.0, "analyst": 3.0}


def test_plan_replicas_and_fit():
    s = c.plan(HOT, 30, spare_gpus=8)
    assert [x.canary_replicas for x in s] == [1, 1, 2, 4]
    assert all(x.fits_spare for x in s)
    tight = c.plan(HOT, 30, spare_gpus=1)
    assert [x.fits_spare for x in tight] == [True, True, False, False]


def test_promote_when_everything_is_fine():
    assert c.evaluate(m(), m(), NB, NB)[0] == "promote"


def test_neighbour_regression_forces_rollback_even_if_canary_is_fine():
    action, why = c.evaluate(m(), m(), NB, {"docsum": 2.0, "analyst": 4.5})
    assert action == "rollback" and "analyst" in why[-1]


def test_quality_drop_rolls_back():
    assert c.evaluate(m(), m(quality=0.8), NB, NB)[0] == "rollback"


def test_too_little_traffic_holds():
    assert c.evaluate(m(), m(requests=10), NB, NB)[0] == "hold"


def test_ladder_stops_where_it_fails_and_when_it_does_not_fit():
    ok = lambda s: (m(), m(), NB, NB)
    assert c.run_ladder(HOT, 30, 8, ok)["action"] == "promote"
    bad = lambda s: (m(), m(error_rate=0.05) if s.weight_pct >= 25 else m(), NB, NB)
    r = c.run_ladder(HOT, 30, 8, bad)
    assert r["action"] == "rollback" and r["at"] == 25
    assert c.run_ladder(HOT, 30, 1, ok)["action"] == "hold"


def test_rollback_order_starts_with_traffic():
    assert c.rollback_order(25)[0].startswith("set canary weight to 0")
    assert c.rollback_order(0) == ["nothing to roll back"]
