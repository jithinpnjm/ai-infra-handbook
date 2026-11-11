import c31_sentinel_sim as ss


def kinds(s):
    return [k for _, _, k in s.actions]


def test_default_is_monitor_only():
    s = ss.Sentinel(ss.Config(gpu_nodes=20))
    s.handle(0, "n1", healthy=False)
    assert s.cordoned == set()
    assert s.conditions["n1"] == "unhealthy"
    assert kinds(s) == ["report_only"]


def test_quarantine_cordons_without_drain_or_remediate():
    s = ss.Sentinel(ss.Config(gpu_nodes=20, quarantine=True))
    s.handle(0, "n1", healthy=False)
    assert kinds(s) == ["cordon"]


def test_remediation_needs_drain_stage():
    s = ss.Sentinel(ss.Config(gpu_nodes=20, quarantine=True, remediate=True))
    s.handle(0, "n1", healthy=False)
    assert "remediate" not in kinds(s)
    s2 = ss.Sentinel(ss.Config(gpu_nodes=20, quarantine=True, drain=True, remediate=True))
    s2.handle(0, "n1", healthy=False)
    assert kinds(s2) == ["cordon", "drain", "remediate"]


def test_dry_run_changes_nothing():
    s = ss.Sentinel(ss.Config(gpu_nodes=20, quarantine=True, drain=True, dry_run=True))
    s.handle(0, "n1", healthy=False)
    assert s.cordoned == set()
    assert kinds(s) == ["would_cordon"]


def test_contact_support_is_never_auto_remediated():
    s = ss.Sentinel(ss.Config(gpu_nodes=20, quarantine=True, drain=True, remediate=True))
    s.handle(0, "n1", healthy=False, action="CONTACT_SUPPORT")
    assert "remediate" not in kinds(s)
    assert "page_human" in kinds(s)


def test_threshold_rounds_up_and_one_node_trips_at_first_cordon():
    assert ss.Sentinel(ss.Config(gpu_nodes=1)).trip_threshold() == 1
    assert ss.Sentinel(ss.Config(gpu_nodes=5)).trip_threshold() == 3
    assert ss.Sentinel(ss.Config(gpu_nodes=20)).trip_threshold() == 10
    s = ss.Sentinel(ss.Config(gpu_nodes=1, quarantine=True))
    s.handle(0, "n1", healthy=False)
    assert s.tripped and s.cordoned == set()


def test_breaker_trips_at_threshold_within_window():
    s = ss.Sentinel(ss.Config(gpu_nodes=10, quarantine=True))
    for i in range(4):
        s.handle(i, f"n{i}", healthy=False)
    assert len(s.cordoned) == 4 and not s.tripped
    s.handle(5, "n4", healthy=False)
    assert s.tripped and "n4" not in s.cordoned


def test_cordons_outside_window_do_not_count():
    s = ss.Sentinel(ss.Config(gpu_nodes=10, quarantine=True))
    for i in range(4):
        s.handle(i * 400, f"n{i}", healthy=False)
    assert not s.tripped and len(s.cordoned) == 4


def test_tripped_breaker_blocks_uncordon_but_not_conditions():
    s = ss.Sentinel(ss.Config(gpu_nodes=2, quarantine=True))
    s.handle(0, "n1", healthy=False)
    assert s.tripped
    s.cordoned.add("n0")
    s.handle(10, "n0", healthy=True)
    assert "n0" in s.cordoned
    assert s.conditions["n0"] == "healthy"
    s.reset_breaker()
    s.handle(20, "n0", healthy=True)
    assert "n0" not in s.cordoned


def test_breaker_disabled_cordons_everything():
    s = ss.Sentinel(ss.Config(gpu_nodes=2, quarantine=True, breaker_enabled=False))
    s.handle(0, "n0", healthy=False)
    s.handle(1, "n1", healthy=False)
    assert s.cordoned == {"n0", "n1"}
