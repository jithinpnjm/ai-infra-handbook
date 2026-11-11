import pytest

import c03_decision as d
import c03_loadgen as lg
import c03_mock_server as ms


@pytest.fixture()
def server():
    state = ms.MockState(ttft_ms=20, itl_ms=5, slots=4)
    srv, st, url = ms.start(state)
    yield st, url
    srv.shutdown()
    srv.server_close()


def test_percentile_nearest_rank():
    vals = list(range(1, 101))
    assert lg.percentile(vals, 50) == 50
    assert lg.percentile(vals, 95) == 95
    assert lg.percentile(vals, 99) == 99
    assert lg.percentile([7], 99) == 7
    assert lg.percentile([], 95) is None
    with pytest.raises(ValueError):
        lg.percentile(vals, 0)


def test_single_request_measures_ttft_and_tpot(server):
    _, url = server
    r = lg.one_request(url, "mock-model", "hello", max_tokens=10)
    assert r.ok and r.tokens == 10
    assert 0.018 <= r.ttft_s < 0.15          # configured 20 ms
    assert 0.004 <= r.tpot_s < 0.05          # configured 5 ms
    assert r.e2e_s >= r.ttft_s


def test_closed_loop_summary(server):
    _, url = server
    res, wall = lg.run_closed(url, "mock-model", concurrency=2, duration_s=1.0,
                              prompt_mean=20, prompt_std=2, max_tokens=8, seed=1)
    s = lg.summarize(res, wall, slo_ttft_ms=500, slo_tpot_ms=100)
    assert s["ok"] == s["requests"] > 5
    assert s["error_rate"] == 0
    assert s["goodput_fraction"] == 1.0
    assert s["output_tok_per_s"] > 0


def test_saturation_raises_ttft_when_more_workers_than_slots(server):
    _, url = server
    low, w1 = lg.run_closed(url, "mock-model", 2, 1.5, 10, 1, 20, 1)
    high, w2 = lg.run_closed(url, "mock-model", 16, 1.5, 10, 1, 20, 1)
    p_low = lg.summarize(low, w1)["ttft_ms"]["p95"]
    p_high = lg.summarize(high, w2)["ttft_ms"]["p95"]
    assert p_high > 3 * p_low      # 16 workers share 4 slots, so requests queue


def test_open_loop_sends_independent_of_responses(server):
    _, url = server
    res, wall = lg.run_open(url, "mock-model", rate=20.0, duration_s=1.5,
                            prompt_mean=10, prompt_std=1, max_tokens=8, seed=3)
    # Poisson at 20 per second for 1.5 s: expect near 30, allow wide noise.
    assert 10 <= len(res) <= 60
    assert all(r.ok for r in res)


def test_errors_are_counted_not_hidden():
    state = ms.MockState(ttft_ms=1, itl_ms=1, slots=4, fail_every=2)
    srv, _, url = ms.start(state)
    try:
        res, wall = lg.run_closed(url, "mock-model", 1, 0.5, 5, 1, 4, 1)
    finally:
        srv.shutdown()
        srv.server_close()
    s = lg.summarize(res, wall)
    assert s["error_rate"] > 0.3
    assert any(r.status == 500 for r in res)


def test_429_when_queue_is_full():
    state = ms.MockState(ttft_ms=200, itl_ms=1, slots=1, max_queue=1)
    srv, _, url = ms.start(state)
    try:
        res, wall = lg.run_closed(url, "mock-model", 6, 1.0, 5, 1, 2, 1)
    finally:
        srv.shutdown()
        srv.server_close()
    assert any(r.status == 429 for r in res)


def test_unreachable_server_is_an_error_not_a_crash():
    r = lg.one_request("http://127.0.0.1:1", "m", "x", 4, timeout_s=1)
    assert not r.ok and r.status == 0


def test_goodput_counts_only_requests_inside_the_objectives(server):
    _, url = server
    res, wall = lg.run_closed(url, "mock-model", 1, 1.0, 10, 1, 8, 1)
    tight = lg.summarize(res, wall, slo_ttft_ms=1, slo_tpot_ms=1)   # impossible objectives
    loose = lg.summarize(res, wall, slo_ttft_ms=1000, slo_tpot_ms=1000)
    assert tight["goodput_fraction"] == 0.0 and tight["good_tok_per_s"] == 0.0
    assert loose["goodput_fraction"] == 1.0


# ---- decision rule ----------------------------------------------------------

def level(c, ttft95, tpot95, err=0.0, frac=1.0, e2e=5.0):
    return {"concurrency": c, "ttft_ms": {"p95": ttft95}, "tpot_ms": {"p95": tpot95},
            "error_rate": err, "goodput_fraction": frac, "mean_e2e_s": e2e}


def test_decision_go_with_headroom_and_littles_law():
    sweep = [level(4, 100, 20), level(8, 150, 22), level(16, 190, 24), level(32, 900, 60, frac=0.3)]
    r = d.decide(sweep, slo_ttft_ms=200, slo_tpot_ms=25, peak_rps=3, max_replicas=2)
    assert r["operating_concurrency"] == 16
    assert r["scale_target"] == 12            # floor(16 * 0.8)
    assert r["concurrent_at_peak"] == pytest.approx(15.0)
    assert r["replicas_needed"] == 2          # ceil(15 / 12)
    assert r["decision"] == "GO"


def test_decision_no_go_when_peak_needs_more_gpus():
    sweep = [level(4, 100, 20), level(8, 150, 22)]
    r = d.decide(sweep, 200, 25, peak_rps=10, max_replicas=2)
    assert r["decision"] == "NO-GO"
    assert r["replicas_needed"] > 2
    assert any("GPUs" in x for x in r["reasons"])


def test_decision_no_go_when_lowest_level_fails():
    r = d.decide([level(1, 500, 80)], 200, 25, 1, 4)
    assert r["decision"] == "NO-GO" and r["operating_concurrency"] is None


def test_pass_above_a_failure_is_ignored():
    sweep = [level(4, 100, 20), level(8, 400, 20), level(16, 100, 20)]
    r = d.decide(sweep, 200, 25, 1, 8)
    assert r["operating_concurrency"] == 4
    assert any("ignored" in x for x in r["reasons"])


def test_errors_alone_fail_a_level():
    ok, why = d.level_passes(level(4, 100, 20, err=0.05), 200, 25, 0.01, 0.95)
    assert not ok and "error rate" in why[0]


def test_bad_headroom_rejected():
    with pytest.raises(ValueError):
        d.decide([level(1, 1, 1)], 200, 25, 1, 1, headroom=1.5)
