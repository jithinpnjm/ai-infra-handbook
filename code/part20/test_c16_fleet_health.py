# code/part20/test_c16_fleet_health.py
import pytest
from c16_fleet_health import (DrainLimiter, Fleet, Node, State, classify_xid)


def make(n=100, **kw):
    nodes = [Node(f"n{i}", f"rack{i % 10}") for i in range(n)]
    return Fleet(nodes, DrainLimiter(n, **kw))


def test_classify_known_and_unknown():
    assert classify_xid(79) == "drain"
    assert classify_xid(43) == "ignore"
    assert classify_xid(999) == "suspect"


def test_app_xid_repeats_become_drain():
    assert classify_xid(13, 0) == "suspect"
    assert classify_xid(13, 2) == "drain"


def test_fallen_off_bus_cordons_node():
    f = make()
    assert f.report_xid("n0", 0, 79) is State.CORDONED


def test_ignored_xid_leaves_node_healthy():
    f = make()
    assert f.report_xid("n0", 0, 63) is State.HEALTHY


def test_repeat_xid13_escalates():
    f = make()
    assert f.report_xid("n0", 0, 13) is State.SUSPECT
    f.report_xid("n0", 10, 13)
    assert f.report_xid("n0", 20, 13) is State.CORDONED


def test_illegal_transition_rejected():
    f = make()
    with pytest.raises(ValueError):
        f.advance("n0", 0, State.REPAIRING)


def test_fleet_budget_holds_extra_nodes():
    f = make(100, max_fraction=0.02, max_per_domain=5, max_per_hour=50)
    for i in range(4):
        f.report_xid(f"n{i}", i, 79)
    assert f.nodes["n0"].state is State.CORDONED
    assert f.nodes["n1"].state is State.CORDONED
    assert f.nodes["n2"].state is State.SUSPECT
    assert f.held["n2"] == "fleet budget exhausted"


def test_domain_budget():
    f = make(100, max_fraction=0.5, max_per_hour=50)
    f.report_xid("n0", 0, 79)
    f.report_xid("n10", 1, 79)  # same rack0
    assert f.nodes["n10"].state is State.SUSPECT
    assert f.held["n10"] == "failure domain budget exhausted"


def test_hourly_rate_resets():
    f = make(100, max_fraction=0.5, max_per_domain=9, max_per_hour=1)
    f.report_xid("n0", 0, 79)
    f.report_xid("n1", 5, 79)
    assert f.nodes["n1"].state is State.SUSPECT
    f.report_xid("n1", 3700, 79)
    assert f.nodes["n1"].state is State.CORDONED


def test_freeze_on_mass_flagging():
    f = make(1000, trip_flags=4, max_fraction=0.5, max_per_domain=9, max_per_hour=99)
    for i in range(6):
        f.report_xid(f"n{i}", i, 79)
    assert f.limiter.frozen
    assert f.nodes["n5"].state is State.SUSPECT
    f.limiter.unfreeze()
    f.report_xid("n5", 100, 79)
    assert f.nodes["n5"].state is State.CORDONED


def test_slot_held_until_node_returns_healthy():
    f = make(100, max_fraction=0.01)
    f.report_xid("n0", 0, 79)
    for to in (State.DRAINING, State.QUARANTINED, State.REPAIRING, State.VALIDATING):
        f.advance("n0", 1, to)
    assert "n0" in f.limiter.out
    f.advance("n0", 2, State.HEALTHY)
    assert "n0" not in f.limiter.out


def test_stuck_detection():
    f = make()
    f.report_xid("n0", 0, 79)
    f.advance("n0", 0, State.DRAINING)
    assert f.stuck(100) == []
    assert f.stuck(3600) == ["n0"]


def test_serving_count():
    f = make(10, max_fraction=0.5, max_per_domain=9)
    f.report_xid("n0", 0, 79)
    assert f.serving() == 9
