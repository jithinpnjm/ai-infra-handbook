"""Tests for c06_node_policy.py and c06_xid_classes.py (chapter 19.6)."""
import csv
import pathlib

import pytest

import c06_node_policy as np_
import c06_xid_classes as xc
from c06_node_policy import (Action, ConditionAgent, Kind, Mode, Node,
                             NodeHealthController, Policy, State, budget, parse_duration)

HERE = pathlib.Path(__file__).parent


def pool(n=4, **policy_kw):
    nodes = [Node(f"gpu-node-{i:02d}", condition=True, since=0, pods=3) for i in range(1, n + 1)]
    pol = Policy(action=Mode.CORDON_AND_DRAIN, max_unavailable="10%", **policy_kw)
    return NodeHealthController(pol, nodes), nodes, ConditionAgent()


def kinds(actions):
    return [(a.kind, a.node, a.detail) for a in actions]


# --- policy shape and the budget ---------------------------------------------------

def test_cordon_and_drain_without_budget_is_rejected():
    with pytest.raises(ValueError, match="maxUnavailableNodes is required"):
        Policy(action=Mode.CORDON_AND_DRAIN)
    Policy(action=Mode.CORDON)  # allowed: Cordon needs no budget


@pytest.mark.parametrize("spec,matched,want", [
    ("10%", 4, 1), ("10%", 32, 4), ("10%", 10, 1), (1, 4, 1), ("50%", 4, 2),
    (99, 4, 4), ("abc", 4, 0), (-3, 4, 0), (None, 4, 4),
])
def test_budget_rounds_up_and_fails_safe(spec, matched, want):
    assert budget(spec, matched) == want


def test_durations():
    assert parse_duration("2m") == 120 and parse_duration("5m") == 300 and parse_duration("1h") == 3600
    with pytest.raises(ValueError):
        parse_duration("2 minutes")


@pytest.mark.parametrize("name", ["c06_gpu_health_policy.yaml", "c06_gpu_health_policy_dryrun.yaml"])
def test_policy_yaml_loads_into_the_model(name):
    pol = Policy.from_yaml_text((HERE / name).read_text())
    assert pol.unhealthy_for == 120 and pol.healthy_for == 300
    if "dryrun" in name:
        assert pol.dry_run and pol.action is Mode.CORDON and pol.max_unavailable == 1
    else:
        assert not pol.dry_run and pol.action is Mode.CORDON_AND_DRAIN and pol.max_unavailable == "10%"


# --- windows and the missing-signal rule --------------------------------------------

def test_blip_inside_the_window_does_nothing():
    ctl, nodes, agent = pool()
    nodes[0].condition, nodes[0].since = False, 100
    assert ctl.reconcile(100 + 60) == []
    assert nodes[0].state is State.PENDING and not nodes[0].unschedulable
    nodes[0].condition, nodes[0].since = True, 170          # recovered before 2 minutes
    ctl.reconcile(200)
    assert nodes[0].state is State.HEALTHY


def test_condition_false_past_the_window_cordons_and_records_owner():
    ctl, nodes, _ = pool()
    nodes[1].condition, nodes[1].since = False, 0
    acts = ctl.reconcile(130)
    assert (Kind.CORDON, "gpu-node-02") in [(a.kind, a.node) for a in acts]
    assert nodes[1].unschedulable and nodes[1].owner == "training-pool"
    assert ctl.reconcile(131) == [] or all(a.kind is not Kind.CORDON for a in ctl.reconcile(132))


def test_missing_signal_never_cordons_and_pages_once():
    ctl, nodes, agent = pool()
    for n in nodes:
        agent.on_signal_lost(n)
    first = ctl.reconcile(1000)
    assert [a.kind for a in first] == [Kind.PAGE]
    assert not any(n.unschedulable for n in nodes)
    assert ctl.reconcile(1060) == []                       # one page, not one per tick


# --- ownership and the return gate --------------------------------------------------

def test_human_cordon_is_never_released():
    ctl, nodes, _ = pool()
    nodes[2].unschedulable = True                          # kubectl cordon by a person
    ctl.reconcile(10_000)
    assert nodes[2].unschedulable and nodes[2].owner is None


def test_owned_cordon_releases_after_the_recovery_window_only():
    ctl, nodes, _ = pool()
    n = nodes[0]
    n.condition, n.since = False, 0
    ctl.reconcile(130)
    n.condition, n.since = True, 200
    assert all(a.kind is not Kind.UNCORDON for a in ctl.reconcile(200 + 299))
    acts = ctl.reconcile(200 + 300)
    assert (Kind.UNCORDON, n.name) in [(a.kind, a.node) for a in acts]
    assert not n.unschedulable and n.owner is None and n.state is State.HEALTHY


def test_signal_loss_after_a_cordon_does_not_return_the_node():
    ctl, nodes, agent = pool()
    n = nodes[0]
    n.condition, n.since = False, 0
    ctl.reconcile(130)
    agent.on_signal_lost(n)
    ctl.reconcile(10_000)
    assert n.unschedulable                                  # not proven healthy


# --- Xid classes, ticket and the diagnostic gate ------------------------------------

def test_xid_79_opens_a_ticket_and_blocks_return_until_diag_and_close():
    ctl, nodes, agent = pool()
    n = nodes[0]
    agent.on_xid(n, 79, now=0)
    acts = ctl.reconcile(130)
    assert Kind.OPEN_TICKET in [a.kind for a in acts] and n.ticket == "RMA-0001"
    assert n.state is State.REPAIR                          # pods drained, ticket open
    # GPU looks healthy for an hour: still not returned.
    agent.on_signal_restored(n, now=200)
    assert all(a.kind is not Kind.UNCORDON for a in ctl.reconcile(200 + 3600))
    ctl.mark_repaired(n.name)
    ctl.record_diag(n.name, passed=False)                   # diag fails: back to repair
    assert n.state is State.REPAIR
    ctl.mark_repaired(n.name)
    ctl.record_diag(n.name, passed=True)
    assert all(a.kind is not Kind.UNCORDON for a in ctl.reconcile(10_000))   # ticket still open
    ctl.close_ticket(n.name)
    assert (Kind.UNCORDON, n.name) in [(a.kind, a.node) for a in ctl.reconcile(10_001)]
    assert n.ticket is None and n.state is State.HEALTHY


def test_diag_result_for_a_node_not_in_validation_is_rejected():
    ctl, nodes, _ = pool()
    with pytest.raises(ValueError):
        ctl.record_diag(nodes[0].name, passed=True)


@pytest.mark.parametrize("xid,cls", [
    (79, xc.UNRECOVERABLE), (48, xc.UNRECOVERABLE), (95, xc.UNRECOVERABLE),
    (13, xc.APPLICATION), (31, xc.APPLICATION), (94, xc.APPLICATION),
    (63, xc.SELF_HEALING), (92, xc.SELF_HEALING), (43, xc.SELF_HEALING),
    (45, xc.SYMPTOM), (74, xc.INTERCONNECT), (61, xc.UNKNOWN), (999, xc.UNKNOWN),
])
def test_xid_classes(xid, cls):
    assert xc.classify_xid(xid) == cls


@pytest.mark.parametrize("xid", [13, 31, 63, 92, 43, 45, 999])
def test_only_unrecoverable_xids_change_the_condition(xid):
    ctl, nodes, agent = pool()
    agent.on_xid(nodes[0], xid, now=0)
    assert nodes[0].condition is True
    assert ctl.reconcile(10_000) == []


def test_xid_74_labels_the_node_and_does_not_cordon():
    ctl, nodes, agent = pool()
    agent.on_xid(nodes[0], 74, now=0)
    assert nodes[0].labels["platform.example.com/nvlink-suspect"] == "true"
    ctl.reconcile(10_000)
    assert not nodes[0].unschedulable


def test_catalog_table_matches_the_snapshot_file():
    lines = [l for l in (HERE / "c06_xid_catalog_snapshot.csv").read_text().splitlines() if not l.startswith("#")]
    snap = {int(r["xid"]): r["immediate_action"] for r in csv.DictReader(lines)}
    assert xc.CATALOG_IMMEDIATE == {k: v for k, v in snap.items() if v != "N/A"}
    assert snap[61] == "N/A"                                # Xid 61 is unused in the catalog
    for xid, immediate in xc.CATALOG_IMMEDIATE.items():
        if immediate in ("RESET_GPU", "RESTART_BM") or xid == 48:
            assert xc.CLASS_OF[xid] == xc.UNRECOVERABLE


# --- budget, rate limit, circuit breaker --------------------------------------------

def test_budget_of_one_cordons_one_and_holds_the_other():
    ctl, nodes, agent = pool()
    for n in nodes[:2]:
        agent.on_xid(n, 79, now=0)
    acts = ctl.reconcile(130)
    assert [a.node for a in acts if a.kind is Kind.CORDON] == ["gpu-node-01"]
    assert (Kind.HOLD, "gpu-node-02", "budget") in kinds(acts)
    assert not nodes[1].unschedulable


def test_a_human_cordon_uses_budget_too():
    ctl, nodes, agent = pool()
    nodes[3].unschedulable = True
    agent.on_xid(nodes[0], 79, now=0)
    acts = ctl.reconcile(130)
    assert (Kind.HOLD, "gpu-node-01", "budget") in kinds(acts)


def test_rate_limit_spaces_out_cordons():
    nodes = [Node(f"n{i:02d}", condition=True, since=0) for i in range(20)]
    pol = Policy(action=Mode.CORDON, max_unavailable="50%", max_new_per_hour=2, breaker_nodes=99)
    ctl, agent = NodeHealthController(pol, nodes), ConditionAgent()
    for n in nodes[:4]:
        agent.on_xid(n, 79, now=0)
    acts = ctl.reconcile(130)
    assert len([a for a in acts if a.kind is Kind.CORDON]) == 2
    assert len([a for a in acts if a == Action(Kind.HOLD, "n02", "rate")]) == 1
    later = ctl.reconcile(130 + 3601)                        # an hour on, the limit refills
    assert [a.node for a in later if a.kind is Kind.CORDON] == ["n02", "n03"]


def test_fleet_wide_fault_trips_the_breaker_and_cordons_nothing():
    nodes = [Node(f"n{i:02d}", condition=True, since=0) for i in range(40)]
    pol = Policy(action=Mode.CORDON_AND_DRAIN, max_unavailable="50%", max_new_per_hour=99)
    ctl, agent = NodeHealthController(pol, nodes), ConditionAgent()
    for n in nodes[:6]:                                      # a bad driver rollout hits six nodes at once
        agent.on_xid(n, 79, now=0)
    acts = ctl.reconcile(130)
    assert ctl.frozen
    assert [a.kind for a in acts if a.kind is Kind.PAGE] == [Kind.PAGE]
    assert not any(a.kind is Kind.CORDON for a in acts)
    assert sum(1 for n in nodes if n.unschedulable) == 0
    assert all(a.detail == "frozen" for a in acts if a.kind is Kind.HOLD)
    assert ctl.reconcile(190) and not any(n.unschedulable for n in nodes)   # still frozen a minute later


def test_breaker_counts_nodes_that_flag_one_after_another():
    nodes = [Node(f"n{i:02d}", condition=True, since=0) for i in range(40)]
    pol = Policy(action=Mode.CORDON, max_unavailable="50%", max_new_per_hour=99)
    ctl, agent = NodeHealthController(pol, nodes), ConditionAgent()
    out = []
    for i in range(4):
        agent.on_xid(nodes[i], 79, now=i * 120)
        out.append(ctl.reconcile(i * 120 + 130))
    cordoned = [a.node for acts in out for a in acts if a.kind is Kind.CORDON]
    assert cordoned == ["n00", "n01"] and ctl.frozen         # the third flag in ten minutes froze it


def test_slow_failures_do_not_trip_the_breaker():
    nodes = [Node(f"n{i:02d}", condition=True, since=0) for i in range(40)]
    pol = Policy(action=Mode.CORDON, max_unavailable="50%", max_new_per_hour=99)
    ctl, agent = NodeHealthController(pol, nodes), ConditionAgent()
    for i in range(4):                                       # one node every 20 minutes
        agent.on_xid(nodes[i], 79, now=i * 1200)
        ctl.reconcile(i * 1200 + 130)
    assert not ctl.frozen and sum(n.unschedulable for n in nodes) == 4


def test_unfreeze_with_acknowledgement_lets_real_faults_proceed():
    nodes = [Node(f"n{i:02d}", condition=True, since=0) for i in range(10)]
    pol = Policy(action=Mode.CORDON, max_unavailable="50%", max_new_per_hour=99)
    ctl, agent = NodeHealthController(pol, nodes), ConditionAgent()
    for n in nodes[:3]:
        agent.on_xid(n, 79, now=0)
    ctl.reconcile(130)
    assert ctl.frozen and not any(n.unschedulable for n in nodes)
    ctl.unfreeze(["n00", "n01"])                             # the human confirms two, not the third
    acts = ctl.reconcile(200)
    assert [a.node for a in acts if a.kind is Kind.CORDON] == ["n00", "n01"]
    assert not nodes[2].unschedulable and not ctl.frozen
    assert (Kind.HOLD, "n02", "awaiting human") in kinds(acts)


# --- modes, dry run, drain paths ----------------------------------------------------

def test_ignore_mode_reports_nothing_and_changes_nothing():
    nodes = [Node("a", condition=False, since=0, pods=2)]
    ctl = NodeHealthController(Policy(action=Mode.IGNORE), nodes)
    assert ctl.reconcile(1000) == []
    assert not nodes[0].unschedulable and nodes[0].pods == 2


def test_dry_run_proposes_but_does_not_change_the_node():
    nodes = [Node("a", condition=False, since=0, pods=2)]
    ctl = NodeHealthController(Policy(action=Mode.CORDON, max_unavailable=1, dry_run=True), nodes)
    acts = ctl.reconcile(1000)
    assert [a.kind for a in acts] == [Kind.WOULD_CORDON]
    assert not nodes[0].unschedulable and nodes[0].owner is None and nodes[0].pods == 2


def test_eviction_respects_a_disruption_budget():
    ctl, nodes, agent = pool()
    n = nodes[0]
    n.pods, n.pdb_blocked = 5, 2
    n.condition, n.since = False, 0
    acts = ctl.reconcile(130)
    assert (Kind.EVICT, n.name, "3 pods") in kinds(acts)
    assert n.pods == 2 and n.state is State.DRAINING          # two pods still protected
    n.pdb_blocked = 0                                         # the service scaled up elsewhere
    acts = ctl.reconcile(190)
    assert (Kind.EVICT, n.name, "2 pods") in kinds(acts) and n.pods == 0
    assert n.state is State.CORDONED                          # drained, no ticket needed


def test_taint_method_taints_instead_of_evicting():
    nodes = [Node("a", condition=False, since=0, pods=4)]
    pol = Policy(action=Mode.CORDON_AND_DRAIN, max_unavailable=1, drain_method="taint")
    ctl = NodeHealthController(pol, nodes)
    acts = ctl.reconcile(1000)
    assert Kind.TAINT in [a.kind for a in acts] and all(a.kind is not Kind.EVICT for a in acts)
    assert nodes[0].tainted and nodes[0].pods == 4            # the kubelet evicts, not the controller
    assert [a.kind for a in ctl.reconcile(1060)].count(Kind.TAINT) == 0   # idempotent


def test_reconcile_is_deterministic_and_idempotent():
    def run():
        ctl, nodes, agent = pool()
        agent.on_xid(nodes[2], 79, now=0)
        return kinds(ctl.reconcile(130)), kinds(ctl.reconcile(131))
    first, second = run(), run()
    assert first == second
    assert not any(k[0] is Kind.CORDON for k in first[1])


def test_illegal_state_move_is_refused():
    ctl, nodes, _ = pool()
    with pytest.raises(ValueError):
        ctl._move(nodes[0], State.REPAIR)


def test_module_exports_the_documented_owner_key():
    assert np_.OWNER_KEY == "platform.example.com/cordoned-by"
