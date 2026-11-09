# code/part20/test_c20_autoscale_sim.py
import pytest

import c20_autoscale_sim as sim


def test_hpa_ratio_rule_worked_example():
    # 4 replicas, 9 waiting per pod against a target of 3: ratio 3.0, so 12 replicas
    assert sim.hpa_desired(4, 9, 3) == 12


def test_hpa_tolerance_deadband():
    assert sim.hpa_desired(10, 10.9, 10) == 10   # inside the 0.1 band
    assert sim.hpa_desired(10, 11.1, 10) == 12   # outside: ceil(10 * 1.11)
    assert sim.hpa_desired(10, 5, 10) == 5


def test_cold_start_budget_and_spare_node():
    p = sim.DEFAULTS
    assert sim.cold_start_s(p, has_node=False) == 240 + 90 + 120 + 30
    assert sim.cold_start_s(p, has_node=True) == 120 + 30


def test_lead_time_headroom():
    # demand grows 3 rps per minute, cold start 8 minutes, 0.8 rps per replica
    assert sim.lead_time_headroom(3, 480, 0.8) == 30


def test_trace_is_deterministic_and_shaped():
    a, b = sim.make_trace("burst"), sim.make_trace("burst")
    assert a == b and len(a) == 3600
    assert sum(a[700:800]) > 4 * sum(a[100:200])
    with pytest.raises(ValueError):
        sim.make_trace("nope")


def test_utilisation_signal_cannot_tell_busy_from_overloaded():
    """The mechanism: the util signal saturates, so 40 and 200 percent load read the same."""
    p = sim.DEFAULTS
    busy = {"util": [min(1.0, 8 / (p["slots"] * p["util_saturation"]))] * 3, "ready": 3,
            "waiting": 0, "running": 24, "starting": 0}
    over = {"util": [1.0] * 3, "ready": 3, "waiting": 500, "running": 48, "starting": 0}
    assert sim.metric_util(busy) == sim.metric_util(over) == 1.0
    assert sim.metric_queue(busy) != sim.metric_queue(over)
    assert sim.metric_inflight(over) > 10 * sim.metric_inflight(busy)


def test_util_policy_overprovisions_steady_load():
    tr = sim.make_trace("steady")
    util = sim.run(tr, "util")
    inflight = sim.run(tr, "inflight")
    assert inflight["gpu_hours"] == 3.0
    assert util["gpu_hours"] > 2 * inflight["gpu_hours"]


def test_queue_depth_alone_lags_a_ramp_but_inflight_does_not():
    tr = sim.make_trace("ramp")
    q, i = sim.run(tr, "queue"), sim.run(tr, "inflight")
    assert i["slo_violation_pct"] < q["slo_violation_pct"]


def test_static_fleet_fails_a_burst():
    r = sim.run(sim.make_trace("burst"), None, static_replicas=3)
    assert r["slo_violation_pct"] > 80


def test_scale_down_window_cuts_flapping():
    tr = sim.make_trace("sawtooth")
    with_window = sim.run(tr, "inflight", down_window_s=300)
    without = sim.run(tr, "inflight", down_window_s=0)
    assert without["direction_flips"] > 3 * max(1, with_window["direction_flips"])
    assert without["replica_starts"] > 3 * with_window["replica_starts"]


def test_drain_prevents_dropped_streams():
    tr = sim.make_trace("sawtooth")
    hard = sim.run(tr, "queue", drain=False)
    soft = sim.run(tr, "queue", drain=True)
    assert hard["dropped_streams"] > 0
    assert soft["dropped_streams"] == 0


def test_spare_nodes_help_but_standing_replicas_help_more():
    tr = sim.make_trace("burst")
    base = sim.run(tr, "inflight")
    spare = sim.run(tr, "inflight", spare_nodes=2)
    standing = sim.run(tr, "inflight", min_r=9)
    assert spare["wait_p99_s"] < base["wait_p99_s"]
    assert standing["wait_p99_s"] < spare["wait_p99_s"]
    assert standing["slo_violation_pct"] == 0


def test_cli_prints_table(capsys):
    assert sim.main(["--trace", "steady"]) == 0
    out = capsys.readouterr().out
    assert "inflight" in out and "gpu_hours" in out
