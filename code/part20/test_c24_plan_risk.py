import json
import os
import subprocess
import sys

import pytest

import c24_plan_risk as pr

HERE = os.path.dirname(os.path.abspath(__file__))
FX = os.path.join(HERE, "c24_fixtures")


def load(name):
    with open(os.path.join(FX, name)) as fh:
        return pr.load_plan(fh.read())


def test_create_plan_is_clean():
    assert pr.analyse(load("c24_plan_create_cluster.json")) == []


def test_delete_nodegroup_is_critical_and_keeps_reason():
    f = pr.analyse(load("c24_plan_delete_nodegroup.json"))
    assert [(x["level"], x["address"]) for x in f] == [
        ("CRITICAL", 'nebius_mk8s_v1_node_group.pool["gpu"]')]
    assert f[0]["reason"] == "delete_because_each_key"


def test_replace_nodegroup_is_critical():
    f = pr.analyse(load("c24_plan_replace_nodegroup.json"))
    assert f[0]["level"] == "CRITICAL" and f[0]["kind"] == "replace"


def test_create_before_destroy_cluster_still_critical():
    f = pr.analyse(load("c24_plan_replace_cluster_cbd.json"))
    assert f[0]["level"] == "CRITICAL" and f[0]["kind"] == "replace-create-first"


def test_scale_up_is_clean_scale_down_is_high():
    assert pr.analyse(load("c24_plan_scale_up.json")) == []
    f = pr.analyse(load("c24_plan_scale_down.json"))
    assert f[0]["level"] == "HIGH" and "6 to 2" in f[0]["message"]


def test_non_stateful_delete_is_medium():
    f = pr.analyse(load("c24_plan_delete_rule_only.json"))
    assert f[0]["level"] == "MEDIUM"


def test_allow_list_suppresses_only_that_address():
    plan = load("c24_plan_delete_nodegroup.json")
    assert pr.analyse(plan, allow={'nebius_mk8s_v1_node_group.pool["gpu"]'}) == []
    assert len(pr.analyse(plan, allow={"something.else"})) == 1


def test_errored_plan_is_critical():
    f = pr.analyse(load("c24_plan_errored.json"))
    assert f[0]["kind"] == "errored"


def test_unknown_format_version_rejected():
    with pytest.raises(pr.PlanError):
        load("c24_plan_bad_format.json")


def test_not_a_plan_rejected():
    with pytest.raises(pr.PlanError):
        pr.load_plan('{"version": 4, "resources": []}')
    with pytest.raises(pr.PlanError):
        pr.load_plan("not json")


def test_unknown_action_list_rejected():
    with pytest.raises(pr.PlanError):
        pr.kind_of(["update", "delete"])


@pytest.mark.parametrize("name,code", [
    ("c24_plan_create_cluster.json", 0),
    ("c24_plan_scale_down.json", 1),
    ("c24_plan_delete_nodegroup.json", 1),
    ("c24_plan_delete_rule_only.json", 0),
    ("c24_plan_bad_format.json", 2),
])
def test_cli_exit_codes(name, code):
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "c24_plan_risk.py"),
                        os.path.join(FX, name)], capture_output=True, text=True)
    assert r.returncode == code, r.stdout + r.stderr


def test_cli_fail_on_medium_catches_rule_delete():
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "c24_plan_risk.py"),
                        os.path.join(FX, "c24_plan_delete_rule_only.json"),
                        "--fail-on", "MEDIUM"], capture_output=True, text=True)
    assert r.returncode == 1


def test_real_fixture_has_documented_keys():
    d = json.load(open(os.path.join(FX, "c24_plan_delete_nodegroup.json")))
    for k in ("format_version", "resource_changes", "planned_values", "configuration"):
        assert k in d
