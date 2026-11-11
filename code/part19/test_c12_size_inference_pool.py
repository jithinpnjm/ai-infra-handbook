import pytest
import c12_size_inference_pool as p


def test_capacity_matches_estimator_directly():
    w = p.WORKLOADS[0]
    cap = p.replica_capacity(w)
    e = p.est
    params, layers, kvh, hd = e.MODELS[w.model]
    mem, bw, tf, _ = e.GPUS["h100"]
    wgb = e.weights_gb(params, 2)
    bpt = e.kv_bytes_per_token(layers, kvh, hd)
    d = e.decode_tps(w.batch, w.in_tokens + w.out_tokens, wgb, bpt, bw)
    pf = e.prefill_tps(tf, 0.4, params)
    rate = e.per_gpu_capacity(w.in_tokens, w.out_tokens, w.batch, pf, d)[0]
    assert cap["rate_qps"] == pytest.approx(rate)


def test_chapter_numbers():
    pl = p.pool_plan()
    assert pl["per_model"]["assistant"]["peak_replicas"] == 4
    assert pl["per_model"]["analyst"]["peak_replicas"] == 4
    assert pl["peak_shared_gpus"] == 22 and pl["dedicated_gpus"] == 25
    assert pl["static_gpus"] == 30 and pl["nodes_at_peak"] == 4


def test_shared_never_needs_more_than_dedicated():
    assert max(p.hourly_gpus()) <= p.dedicated_gpus()
    pl = p.pool_plan()
    assert pl["usd_month_autoscaled"] < pl["usd_month_static"] < pl["usd_month_dedicated"]
    assert pl["util_autoscaled"] > pl["util_static"]


def test_min_replicas_floor_holds_at_zero_traffic():
    w = p.WORKLOADS[0]
    assert p.replicas_at(w, 0) == w.min_replicas == 2
    assert p.replicas_at(p.WORKLOADS[1], 0) == 0


def test_model_that_does_not_fit_raises():
    big = p.Workload("big", "qwen2.5-72b", "warm", 1, 3000, 600, 16, tp=1)
    with pytest.raises(ValueError, match="do not fit"):
        p.replica_capacity(big)


def test_pack_keeps_tp_replicas_on_one_node():
    nodes = p.pack_nodes([4, 4, 4, 4, 1, 1, 1, 1])
    assert all(sum(n) <= 8 for n in nodes)
    assert sorted(sum(nodes, [])) == [1, 1, 1, 1, 4, 4, 4, 4]
    assert len(nodes) == 3
    with pytest.raises(ValueError):
        p.pack_nodes([9])


def test_lru_cache_evicts_least_recently_used():
    load = {m: p.cold_load_s(w) for m, w in p.COLD_MODELS.items()}
    c = p.ModelCache(2, load)
    assert c.request("contracts-8b") > 0
    c.request("hr-8b")
    assert c.request("contracts-8b") == 0
    c.request("finance-8b")
    assert c.evictions == ["hr-8b"]
    assert 0 < c.hit_rate() < 1
    with pytest.raises(KeyError):
        c.request("nope")


def test_one_slot_thrashes_with_alternating_models():
    load = {m: 60.0 for m in p.COLD_MODELS}
    c = p.ModelCache(1, load)
    for m in ["contracts-8b", "hr-8b"] * 5:
        c.request(m)
    assert c.hit_rate() == 0 and c.wait_s == 600


def test_cost_formula_and_utilisation_lever():
    a = p.WORKLOADS[0]
    full = p.cost_per_m_output(a, 1.0)
    assert full == pytest.approx(0.45, abs=0.01)
    assert p.cost_per_m_output(a, 0.5) == pytest.approx(2 * full)


def test_cold_slots_trade_gpus_for_waiting():
    r = [p.cold_demo(n) for n in (1, 2, 3)]
    assert r[0]["wait_s"] > r[1]["wait_s"] > r[2]["wait_s"]
    assert r[2]["evictions"] == 0 and r[2]["wait_s"] == 3 * p.cold_load_s(16.4)
