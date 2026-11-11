import random
from c36_node_lifecycle import Cluster, classify

BAD = "[node_problem] gpu_health_check: xid"


def names(n):
    return [f"worker-{i}" for i in range(n)]


def test_classify_known_reasons():
    assert classify("[node_problem] x") == "replace"
    assert classify("[hardware_problem] x") == "replace"
    assert classify("[user_problem] disk full") == "none"
    assert classify("Kill task failed") == "reboot"
    assert classify("[compute_maintenance] node replacement process") == "maintenance"


def test_first_match_wins_in_list_order():
    assert classify("Kill task failed [node_problem]") == "reboot"
    assert classify("[node_problem] and [user_problem]") == "replace"


def test_unknown_reasons_are_never_automated():
    assert classify("Prolog error") == "none"
    assert classify("[software_problem] libcuda") == "none"
    assert classify("") == "none"


def test_waits_for_jobs_before_suspecting_hardware():
    c = Cluster(names(2))
    c.run_job("worker-0", 10)
    c.drain("worker-0", BAD)
    for _ in range(9):
        c.tick()
        assert not c.nodes["worker-0"].hw_suspected
        assert c.nodes["worker-0"].state == "ready"
    for _ in range(3):
        c.tick()
    assert c.nodes["worker-0"].hw_suspected


def test_budget_caps_concurrent_replacements():
    c = Cluster(names(6), max_unavailable=2, reports_per_window=100)
    for n in names(5):
        c.drain(n, BAD)
    for _ in range(120):
        c.tick()
    assert c.max_concurrent == 2
    assert all(n.instance == 2 for n in list(c.nodes.values())[:5])


def test_report_rate_limit_spaces_replacements():
    c = Cluster(names(4), max_unavailable=4, reports_per_window=1, report_window=10)
    for n in names(3):
        c.drain(n, BAD)
    for _ in range(60):
        c.tick()
    gaps = [b - a for a, b in zip(c.reports, c.reports[1:])]
    assert len(c.reports) == 3
    assert all(g >= 10 for g in gaps)


def test_exhausted_report_limit_leaves_node_drained_not_replaced():
    c = Cluster(names(2), max_unavailable=2, reports_per_window=1, report_window=1000)
    c.drain("worker-0", BAD)
    c.drain("worker-1", BAD)
    for _ in range(50):
        c.tick()
    waiting = c.nodes["worker-1"]
    assert waiting.drain_reason and not waiting.hw_suspected and waiting.state == "ready"
    assert c.capacity() < 2


def test_oldest_failure_is_replaced_first():
    c = Cluster(names(3), max_unavailable=1, reports_per_window=100)
    c.drain("worker-2", BAD)
    c.tick()
    c.drain("worker-0", BAD)
    c.tick()
    first = [e for e in c.log if e[2] == "hardware-issues-suspected"][0]
    assert first[1] == "worker-2"


def test_stale_drain_is_cleared_on_new_instance():
    c = Cluster(names(1), replace_minutes=3, join_minutes=2)
    c.drain("worker-0", BAD)
    for _ in range(12):
        c.tick()
    n = c.nodes["worker-0"]
    assert n.instance == 2 and n.drain_reason == "" and n.schedulable(c.now)
    assert (any(e[2] == "undrain-stale" for e in c.log))


def test_user_problem_stays_drained():
    c = Cluster(names(1))
    c.drain("worker-0", "[user_problem] leftover processes")
    for _ in range(200):
        c.tick()
    n = c.nodes["worker-0"]
    assert n.drain_reason and n.instance == 1 and n.state == "ready"


def test_not_ready_node_is_deleted_after_timeout():
    c = Cluster(names(1), not_ready_timeout=15)
    c.go_not_ready("worker-0")
    for _ in range(14):
        c.tick()
    assert c.nodes["worker-0"].state == "ready"
    c.tick()
    c.tick()
    assert c.nodes["worker-0"].state == "replacing"


def test_random_failures_keep_invariants():
    rng = random.Random(36)
    c = Cluster(names(12), max_unavailable=3, reports_per_window=2, report_window=15)
    for _ in range(400):
        if rng.random() < 0.08:
            n = rng.choice(names(12))
            if not c.nodes[n].drain_reason and c.nodes[n].state == "ready":
                c.run_job(n, rng.randint(1, 30))
                c.drain(n, rng.choice([BAD, "[user_problem] x", "[hardware_problem] y"]))
        c.tick()
        assert c.in_flight() <= 3
        for n in c.nodes.values():
            if n.hw_suspected:
                assert not n.running_jobs(c.now)
        recent = [t for t in c.reports if t > c.now - 15]
        assert len(recent) <= 2
