"""Offline tests for the observability capstone (Chapter 19.7).
Need promtool and amtool on PATH. Run: python3 -m pytest code/part19/test_c07_observability.py -q
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

import pytest
import yaml

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import c07_cardinality_budget as card  # noqa: E402
import c07_dashboard_check as dash  # noqa: E402
import c07_prometheusrule as pr  # noqa: E402
import c07_signals as sig  # noqa: E402
import c07_synth_exporter as synth  # noqa: E402

pytestmark = pytest.mark.skipif(not (shutil.which("promtool") and shutil.which("amtool")),
                                reason="promtool and amtool needed")
DASH = HERE / "c07_dashboard_gpu_platform.json"


def sh(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    return r.returncode, r.stdout + r.stderr


# ---- rules -------------------------------------------------------------------------------
def test_rules_check_and_unit_tests_pass():
    assert sh("promtool", "check", "rules", "c07_stack_rules.yaml", "c07_e2e_rules.yaml")[0] == 0
    assert sh("promtool", "test", "rules", "c07_rules_test.yaml")[0] == 0


def test_unit_tests_catch_a_changed_threshold(tmp_path):
    rules = (HERE / "c07_stack_rules.yaml").read_text().replace("> 85", "> 95")
    f = HERE / "_mut_rules.yaml"
    t = HERE / "_mut_test.yaml"
    try:
        f.write_text(rules)
        t.write_text((HERE / "c07_rules_test.yaml").read_text().replace("c07_stack_rules.yaml", f.name)
                     .replace("'90x40'", "'90x40'"))
        # temperature 90 is still above 95? no: 90 < 95, so the firing case must now fail
        code, out = sh("promtool", "test", "rules", t.name)
    finally:
        f.unlink(missing_ok=True)
        t.unlink(missing_ok=True)
    assert code != 0 and "GPUTemperatureHigh" in out


def test_every_alert_has_runbook_and_known_severity():
    docs = yaml.safe_load((HERE / "c07_stack_rules.yaml").read_text())
    alerts = [r for g in docs["groups"] for r in g["rules"] if "alert" in r]
    assert len(alerts) == 9
    for a in alerts:
        assert a["labels"]["severity"] == "ticket", a["alert"]     # only burn alerts page
        assert a["annotations"]["runbook"].startswith("runbooks/")


def test_every_alert_in_the_rule_file_has_a_unit_test():
    docs = yaml.safe_load((HERE / "c07_stack_rules.yaml").read_text())
    names = {r["alert"] for g in docs["groups"] for r in g["rules"] if "alert" in r}
    tests = yaml.safe_load((HERE / "c07_rules_test.yaml").read_text())
    tested = {a["alertname"] for t in tests["tests"] for a in t["alert_rule_test"]}
    assert names <= tested


# ---- SLO scenarios: promtool vs the Python model ------------------------------------------
@pytest.mark.parametrize("sc", sig.SCENARIOS, ids=lambda s: s.name)
def test_scenario_promtool_matches_python_model(sc):
    ok, out = sig.run_promtool(sc)
    assert ok, out


def test_model_values_for_the_blip_scenario():
    blip = sig.SCENARIOS[3]
    assert sig.model_alerts(blip, 2) == {sig.ALERT_FAST, sig.ALERT_SLOW}
    assert sig.model_alerts(blip, 10) == {sig.ALERT_SLOW}       # short window of fast is clean
    assert sig.model_alerts(blip, 65) == set()


def test_promtool_rejects_a_wrong_expectation(tmp_path):
    sc = sig.SCENARIOS[1]
    text = sig.promtool_test(sc).replace("exp_alerts:\n          - exp_labels", "exp_alerts: []\n        _x:\n          - exp_labels", 1)
    f = HERE / "_wrong_test.yaml"
    try:
        f.write_text(text)
        code, _ = sh("promtool", "test", "rules", f.name)
    finally:
        f.unlink(missing_ok=True)
    assert code != 0


# ---- Alertmanager ---------------------------------------------------------------------------
@pytest.mark.parametrize("labels,receiver", [
    (["alertname=Watchdog"], "deadman"),
    (["alertname=X", "severity=page"], "oncall-page"),
    (["alertname=X", "severity=ticket"], "ticket-queue"),
    (["alertname=X"], "ticket-queue"),
])
def test_routes(labels, receiver):
    code, out = sh("amtool", "config", "routes", "test", "--config.file=c07_alertmanager.yaml", *labels)
    assert code == 0 and out.strip() == receiver


def test_amtool_rejects_a_route_to_an_unknown_receiver(tmp_path):
    cfg = yaml.safe_load((HERE / "c07_alertmanager.yaml").read_text())
    cfg["route"]["routes"][0]["receiver"] = "nobody"
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(cfg))
    assert sh("amtool", "check-config", str(p))[0] != 0


def test_no_inline_secrets_in_alertmanager_config():
    text = (HERE / "c07_alertmanager.yaml").read_text()
    assert not re.search(r"^\s*(routing_key|service_key|api_url|url|password):", text, re.M)
    assert text.count("_file:") == 3


# ---- dashboard ----------------------------------------------------------------------------------
def test_dashboard_passes():
    errs, n = dash.check_all(DASH)
    assert errs == [] and n == 11


def _mutate(fn, tmp_path):
    d = json.loads(DASH.read_text())
    fn(d)
    p = tmp_path / "d.json"
    p.write_text(json.dumps(d))
    return dash.check_all(p)[0]


def test_dashboard_broken_promql_is_reported(tmp_path):
    errs = _mutate(lambda d: d["panels"][0]["targets"][0].update(expr="sum by (node (x)"), tmp_path)
    assert any("panel 1" in e and "does not parse" in e for e in errs)


def test_dashboard_undeclared_variable_is_reported(tmp_path):
    errs = _mutate(lambda d: d["panels"][4]["targets"][0].update(expr="up{job=~\"$job\"}"), tmp_path)
    assert any("$job" in e for e in errs)


def test_dashboard_duplicate_id_overlap_and_datasource(tmp_path):
    def f(d):
        d["panels"][1]["id"] = 1
        d["panels"][2]["gridPos"] = dict(d["panels"][0]["gridPos"])
        d["panels"][3]["datasource"] = {"type": "prometheus", "uid": "nope"}
    errs = _mutate(f, tmp_path)
    assert any("duplicate panel ids" in e for e in errs)
    assert any("overlaps" in e for e in errs)
    assert any("'nope'" in e for e in errs)


def test_dashboard_uses_only_dcgm_4_9_names():
    text = DASH.read_text()
    assert "DCGM_FI_DEV_GPU_UTIL_RATIO" in text
    assert not re.search(r"DCGM_FI_DEV_(GPU_UTIL|FB_USED|GPU_TEMP|XID_ERRORS)\b", text)


# ---- cardinality ------------------------------------------------------------------------------------
def test_cardinality_numbers():
    ok, rep = card.check_spec(json.loads((HERE / "c07_metric_spec.json").read_text()))
    assert ok
    assert rep["declared"] == 16700 and rep["used"] == 1016700 and rep["headroom"] == 983300
    assert dict(rep["families"])["DCGM_default_fields_26"] == 26 * 8 * 50


def test_cardinality_rejects_user_id_and_over_budget():
    ok, rep = card.check_spec(json.loads((HERE / "c07_metric_spec_bad.json").read_text()))
    assert not ok and rep["headroom"] < 0
    assert any("user_id" in e for e in rep["lint_errors"])


def test_cardinality_fails_when_reserved_share_is_too_big():
    spec = json.loads((HERE / "c07_metric_spec.json").read_text())
    spec["reserved_for_kubernetes"] = 1_990_000
    assert not card.check_spec(spec)[0]


def test_exposition_lint():
    ok, errs = card.check_exposition(synth.State().render())
    assert ok, errs
    ok, errs = card.check_exposition('# TYPE x_total counter\nx_total{request_id="a1"} 1\n')
    assert not ok and "request_id" in errs[0]


# ---- synthetic exporter and PrometheusRule ----------------------------------------------------------------
def test_exporter_injection():
    s = synth.State(nodes=("n1",), gpus=1)
    assert 'DCGM_FI_DEV_XID_ERROR{node="n1",gpu="0"} 0.0' in s.render()
    s.apply({"xid": {"node": "n1", "gpu": 0, "value": 79}, "probe": 1})
    text = s.render()
    assert 'DCGM_FI_DEV_XID_ERROR{node="n1",gpu="0"} 79.0' in text
    assert "c07_synthetic_probe 1" in text


def test_exporter_error_ratio_moves_the_bad_counter():
    s = synth.State(models=("m1",))
    s.apply({"rps": 1000, "error_ratio": 1.0})
    s.last -= 2.0                                   # pretend two seconds passed
    s.render()
    assert s.bad["m1"] > 1500 and s.good["m1"] < 100


def test_prometheusrule_wrapper_roundtrip_and_failure():
    text = (HERE / "c07_stack_rules.yaml").read_text()
    obj = pr.wrap(text, "c07-stack-rules")
    assert obj["kind"] == "PrometheusRule"
    assert obj["spec"]["groups"] == yaml.safe_load(text)["groups"]
    with pytest.raises(ValueError):
        pr.wrap("foo: bar", "x")


def test_prometheusrule_validates_against_crd_schema(tmp_path):
    if not shutil.which("kubeconform"):
        pytest.skip("kubeconform missing")
    f = tmp_path / "pr.yaml"
    f.write_text(yaml.safe_dump(pr.wrap((HERE / "c07_stack_rules.yaml").read_text(), "c07")))
    r = subprocess.run(["kubeconform", "-strict", "-summary", "-schema-location", "default",
                        "-schema-location",
                        "https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json",
                        str(f)], capture_output=True, text=True)
    if "failed downloading" in r.stdout + r.stderr or "could not find schema" in r.stdout + r.stderr:
        pytest.skip("CRD schema not reachable")
    assert r.returncode == 0, r.stdout + r.stderr


# ---- end to end (Docker, a few minutes) -------------------------------------------------------
@pytest.mark.skipif(not __import__("os").environ.get("C07_E2E"), reason="set C07_E2E=1 to run the Docker end-to-end test")
def test_end_to_end():
    import c07_e2e
    res = c07_e2e.run_e2e()
    assert res and all(r.ok for r in res), [r for r in res if not r.ok]


def test_disk_estimate_for_the_series_budget():
    import c15_cardinality as c15
    spec = json.loads((HERE / "c07_metric_spec.json").read_text())
    total = c15.estimate(spec)["total"]
    assert round(c15.disk_bytes(total, 30, 1296000, 2.0) / 1e9, 2) == 1.44
    full = total + spec["reserved_for_kubernetes"]
    assert round(c15.disk_bytes(full, 30, 1296000, 1.0) / 1e9, 1) == 43.9
    assert round(c15.disk_bytes(full, 30, 1296000, 2.0) / 1e9, 1) == 87.8   # above the 80 GB size cap
