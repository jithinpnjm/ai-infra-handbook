"""Part 17 tests. Run: python3 -m pytest -q code/part17/test_part17.py
Scripts run offline against files under $OPS_HOME; promtool, amtool and kubeconform are used when installed."""
import json, os, shutil, subprocess, sys, hashlib
from datetime import date, datetime, timezone
from pathlib import Path
import pytest, yaml
HERE = Path(__file__).parent; sys.path.insert(0, str(HERE))
import opslib as O

@pytest.fixture(autouse=True)
def ops(tmp_path, monkeypatch):
    monkeypatch.setenv("OPS_HOME", str(tmp_path / "ops")); monkeypatch.chdir(tmp_path); return tmp_path

def outbox(): return [json.loads(l) for l in (O.home() / "outbox.jsonl").read_text().splitlines()]

# ---- capacity and cost ----------------------------------------------------------
def test_capacity_plan_examples_from_chapter():
    import capacity_plan as c
    assert c.plan(100, 0.20, 0.30) == (156, 56)
    assert c.plan(4, 0.20, 0.30) == (7, 3)          # 6.24 rounds UP to 7; the chapter said 6
    assert c.plan(10, 0.0, 0.0) == (10, 0)

def test_forecast_and_cost():
    import workload_forecast as w, cost_forecast as c
    f = w.forecast_workloads({"train": {"current_gpus": 100, "growth_rate": 0.2}}, horizon_days=180)
    assert abs(f["train"]["projected_gpus"] - 144.0) < 1e-9
    assert c.forecast_cost(f, 2.0) == pytest.approx(144 * 2.0 * 24 * 30)

def test_right_size(tmp_path):
    import right_size as r
    rows = [{"workload": "a", "gpus": 8, "avg_util": 0.35}, {"workload": "b", "gpus": 4, "avg_util": 0.9}]
    out = r.recommend(rows); assert (out[0]["recommended"], out[0]["action"]) == (4, "shrink") and out[1]["action"] == "keep"
    (O.home() / "utilisation.json").write_text(json.dumps(rows)); assert r.main(["--cluster", "c", "--output", "r.md"]) == 0 and "| a | 8 | 35% | 4 | shrink |" in open("r.md").read()

# ---- RPO / RTO -------------------------------------------------------------------
def test_rpo_rto_examples_from_chapter(capsys):
    import measure_rpo, measure_rto
    assert measure_rpo.main(["--last-backup", "2024-03-15T13:55:00Z", "--disaster-time", "2024-03-15T14:00:00Z"]) == 1
    assert "RPO is 5 minutes; OUTSIDE the 1m target" in capsys.readouterr().out
    assert measure_rto.main(["--incident-start", "2024-03-15T14:00:00Z", "--incident-end", "2024-03-15T14:45:00Z"]) == 0
    assert "RTO is 45 minutes; within" in capsys.readouterr().out
    assert measure_rto.main(["--incident-start", "2024-03-15T15:00:00Z", "--incident-end", "2024-03-15T14:45:00Z"]) == 2

def test_duration_parser():
    assert O.parse_duration("4h").total_seconds() == 14400 and O.parse_duration("90m").total_seconds() == 5400
    with pytest.raises(ValueError): O.parse_duration("soon")

# ---- backups with real files -----------------------------------------------------
def make_backup(name="backup-1", taken="2024-03-15T13:00:00Z", corrupt=False):
    d = O.home() / "backups" / name; d.mkdir(parents=True)
    files = {"a.db": b"alpha", "b.db": b"beta"}; [(d / k).write_bytes(v) for k, v in files.items()]
    (d / "MANIFEST.json").write_text(json.dumps({"taken_at": taken, "files": {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}}))
    if corrupt: (d / "b.db").write_bytes(b"BAD")

def test_restore_and_verify_backup(capsys):
    import restore_backup, verify_backup
    make_backup(); now = datetime(2024, 3, 15, 13, 30, tzinfo=timezone.utc)
    assert restore_backup.main(["--backup", "backup-1", "--target", "staging"]) == 0 and (O.home() / "restore/staging/a.db").read_bytes() == b"alpha"
    assert verify_backup.main(["--backup", "backup-1", "--expected-rto", "4h", "--expected-rpo", "1h"], now=now) == 0
    assert verify_backup.main(["--backup", "backup-1", "--expected-rto", "4h", "--expected-rpo", "10m"], now=now) == 1     # 30 min old > 10 min RPO
    assert restore_backup.main(["--backup", "backup-1", "--target", "production"]) == 1

def test_corrupt_backup_detected():
    import verify_backup
    make_backup(corrupt=True); assert verify_backup.main(["--backup", "backup-1", "--expected-rto", "4h", "--expected-rpo", "1h"]) == 1

# ---- notices ---------------------------------------------------------------------
def test_announcements_and_status():
    import announce_upgrade as u, announce_rollback as r, send_status_update as s
    args = ["--date", "2024-04-13", "--time", "02:00-06:00 UTC", "--change", "Driver 550.54.15", "--rollback", "to 550.54.14 if SLO breach"]
    assert u.main(args, today=date(2024, 4, 1)) == 0 and u.main(args, today=date(2024, 5, 1)) == 1
    assert r.main(["--change", "x", "--reason", "p99", "--impact", "latency"]) == 0
    assert s.main(["--incident-id", "I", "--severity", "SEV-2", "--status", "mitigating"]) == 0 and s.main(["--incident-id", "I", "--severity", "high", "--status", "x"]) == 1
    assert [o["kind"] for o in outbox()] == ["upgrade_announcement", "rollback_announcement", "status_update"]

def test_schedules_validate_input():
    import schedule_game_day as g, schedule_drill as d, schedule_review as r
    assert g.main(["--date", "2024-04-15", "--time", "14:00 UTC", "--scenario", "GPU Node Failure", "--participants", "platform-team"]) == 0
    assert g.main(["--date", "2024-04-15", "--time", "14:00 UTC", "--scenario", "x", "--participants", ""]) == 1
    with pytest.raises(ValueError): d.main(["--date", "15/04/2024", "--time", "t", "--scenario", "s"])
    assert r.main(["--incident-id", "I", "--date", "2024-03-20", "--attendees", "a,b"]) == 0

def test_post_mortem_templates(tmp_path):
    import generate_post_mortem as p, generate_dr_post_mortem as d
    assert p.main(["--incident-id", "INC-2024-03-15-001", "--output", "pm.md"]) == 0 and "Date of incident: 2024-03-15" in open("pm.md").read()
    assert p.main(["--incident-id", "bad", "--output", "x.md"]) == 1 and d.main(["--drill-id", "DR-2024-03-15", "--output", "dr.md"]) == 0 and d.main(["--drill-id", "x", "--output", "y.md"]) == 1

def test_verify_upgrade_slo():
    import verify_upgrade as v
    (O.home() / "slo.json").write_text(json.dumps({"availability": 0.9995, "p99_ms": 820})); assert v.main(["--change", "c"]) == 0
    (O.home() / "slo.json").write_text(json.dumps({"availability": 0.9995, "p99_ms": 1400})); assert v.main(["--change", "c"]) == 1

# ---- game days -------------------------------------------------------------------
def test_game_day_detects_late_response(capsys):
    import execute_game_day as g, execute_drill as d
    assert g.main(["--scenario", "GPU Node Failure"]) == 0
    assert g.main(["--scenario", "GPU Node Failure", "--detection-delay", "10"]) == 1 and "LATE" in capsys.readouterr().out
    assert g.main(["--scenario", "Meteor"]) == 1 and d.main(["--scenario", "Regional Outage"]) == 0

# ---- checklists, runbooks, catalogue ----------------------------------------------
NOW = datetime(2024, 6, 1, tzinfo=timezone.utc)

def test_checklist_flow():
    import checklist_update as u, checklist_score as s, checklist_review as r, checklist_audit as a
    O.save_yaml("checklist.yaml", [{"id": "HW-001", "name": "ECC alert", "category": "hardware", "status": "active", "last_reviewed": "2024-05-01"},
                                    {"id": "NET-001", "name": "IB errors", "category": "network", "status": "active", "last_reviewed": "2023-01-01"},
                                    {"id": "OLD-1", "name": "gone", "category": "hardware", "status": "retired", "last_reviewed": "2020-01-01"}])
    O.save_yaml("answers.yaml", {"HW-001": "yes"})
    cat, missing = s.score(O.load_yaml("checklist.yaml", []), O.load_yaml("answers.yaml", {}))
    assert cat == {"hardware": [1, 1], "network": [0, 1]} and missing == ["NET-001"]
    assert s.main(["--cluster", "c", "--output", "s.md"]) == 0 and "network: 0/1 (0%)" in open("s.md").read()
    assert r.main(["--staleness-threshold-days", "90"], now=NOW) == 1
    assert u.main(["--item-id", "HW-016", "--name", "n", "--detection-signal", "DCGM_X", "--category", "hardware"]) == 0 and u.main(["--item-id", "HW-016", "--name", "n", "--detection-signal", "s", "--category", "c"]) == 1
    assert a.main(["--cluster", "c"]) == 0

def test_runbook_freshness_gate_and_update():
    import runbook_freshness as f, runbook_update as u, runbook_review as r
    O.save_yaml("runbooks.yaml", [{"url": "https://w/gpu-mem", "last_reviewed": "2024-05-20", "failure_mode": "FM-001"}, {"url": "https://w/old", "last_reviewed": "2023-01-01"}])
    assert f.main(["--staleness-threshold-days", "90"], now=NOW) == 1
    assert u.main(["--runbook-url", "https://w/old", "--incident-id", "I", "--new-mitigation", "reduce batch"]) == 0 and u.main(["--runbook-url", "nope", "--incident-id", "I", "--new-mitigation", "x"]) == 1
    assert f.main(["--staleness-threshold-days", "90"], now=NOW) == 0
    O.save_yaml("catalogue.yaml", [{"id": "FM-001"}, {"id": "FM-002"}]); assert r.main([]) == 0

def test_catalogue_counts_repeats(capsys):
    import update_catalogue as u, review_catalogue as r
    for i in range(3): assert u.main(["--incident-id", f"I{i}", "--failure-mode", "FM-001", "--runbook-url", "u", "--last-incident", "2024-03-15"]) == 0
    r.main([], now=NOW); out = capsys.readouterr().out; assert "repeated (3+ incidents): ['FM-001']" in out

def test_renewals_sorted(tmp_path):
    import renewal_calendar as rc
    O.save_yaml("commitments.yaml", [{"name": "b", "level": "3y", "expires": "2026-01-01"}, {"name": "a", "level": "1y", "expires": "2025-01-01"}])
    rc.main(["--cluster", "c", "--output", "cal.md"]); t = open("cal.md").read(); assert t.index("| a |") < t.index("| b |") if "| a |" in t else t.index("2025") < t.index("2026")

def test_correlate_profile():
    import correlate_profile as c
    assert c.main(["--profile", "p.json", "--trace-id", "abc123"]) == 0 and c.main(["--profile", "p", "--trace-id", "XYZ"]) == 1
    assert json.loads((O.home() / "profile_index.json").read_text()) == {"abc123": ["p.json"]}

# ---- fragments that now run -------------------------------------------------------
def test_log_trace_runbook_helpers():
    import log_analysis as la, trace_correlation as tc, runbook_validation as rv, runbook_generation as rg, root_cause_analysis as rca
    r = la.analyze_logs(["ERROR boom", "WARN slow", "ERROR x Traceback", "info"]); assert len(r["errors"]) == 2 and len(r["warnings"]) == 1 and len(r["exceptions"]) == 1
    assert tc.correlate_traces([{"trace_id": "t", "spans": [{"span_id": "s", "name": "n", "duration_ms": 1500}, {"span_id": "q", "name": "m", "duration_ms": 10}]}])[0]["span_id"] == "s"
    good = "\n".join(f"## {s}" for s in rv.REQUIRED_SECTIONS) + "\n$ kubectl get pods\n"
    assert rv.validate_runbook(good) == (True, []) and not rv.validate_runbook("## Symptoms\nlook around")[0]
    class LLM:
        def __init__(self, t): self.t = t
        def complete(self, p): return self.t
    assert rg.generate_runbook(LLM(good), "t", []) == good
    with pytest.raises(ValueError): rg.generate_runbook(LLM("## Symptoms"), "t", [])
    hy = json.dumps([{"hypothesis": "h1", "evidence": "e", "mitigation": "m", "confidence": 2}, {"hypothesis": "h2", "evidence": "e", "mitigation": "m", "confidence": 5}])
    assert rca.analyze_root_cause(LLM(hy), [], [], {}, [])[0]["hypothesis"] == "h2"
    for bad in ("not json", json.dumps([{"hypothesis": "x"}]), json.dumps([{"hypothesis": "h", "evidence": "e", "mitigation": "m", "confidence": 9}])):
        with pytest.raises(ValueError): rca.analyze_root_cause(LLM(bad), [], [], {}, [])

# ---- config validation with the real tools ----------------------------------------
def tool(name):
    p = shutil.which(name) or str(Path.home() / "go/bin" / name); return p if Path(p).exists() else None

@pytest.mark.skipif(not tool("promtool"), reason="promtool not installed")
def test_prometheus_rules_and_scrape_config():
    r = subprocess.run([tool("promtool"), "check", "rules", str(HERE / "gpu_alerts.yaml"), str(HERE / "recording_rules.yaml")], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr
    r = subprocess.run([tool("promtool"), "check", "config", str(HERE / "prometheus_scrape.yaml")], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr

@pytest.mark.skipif(not tool("amtool"), reason="amtool not installed")
def test_alertmanager_config():
    r = subprocess.run([tool("amtool"), "check-config", str(HERE / "alertmanager.yaml")], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr

def dashboard_exprs():
    out = []
    for p in sorted(HERE.glob("*dashboard*.json")):
        d = json.loads("\n".join(l for l in p.read_text().splitlines() if not l.lstrip().startswith("//")))
        def walk(o):
            if isinstance(o, dict):
                if "expr" in o and isinstance(o["expr"], str) and not o["expr"].startswith("{"): out.append((p.name, o["expr"]))   # "{...}" is LogQL, not PromQL
                [walk(v) for v in o.values()]
            elif isinstance(o, list): [walk(v) for v in o]
        walk(d)
    return out

def test_dashboards_are_json_with_panels():
    ps = sorted(HERE.glob("*dashboard*.json")); assert ps
    for p in ps:
        d = json.loads("\n".join(l for l in p.read_text().splitlines() if not l.lstrip().startswith("//")))
        assert d.get("title") or d.get("dashboard", {}).get("title"), p.name

@pytest.mark.skipif(not tool("promtool"), reason="promtool not installed")
def test_dashboard_promql_parses(tmp_path):
    ex = [(n, e.replace("$__rate_interval", "5m").replace("$__interval", "5m")) for n, e in dashboard_exprs()]
    assert ex, "no PromQL expressions found in dashboards"
    rules = {"groups": [{"name": "d", "rules": [{"record": f"r{i}", "expr": e} for i, (_, e) in enumerate(ex)]}]}
    f = tmp_path / "r.yaml"; f.write_text(yaml.safe_dump(rules))
    r = subprocess.run([tool("promtool"), "check", "rules", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr

@pytest.mark.skipif(not tool("kubeconform"), reason="kubeconform not installed")
def test_core_k8s_manifests_validate():
    files = [str(p) for p in HERE.glob("*.yaml") if "\nkind:" in "\n" + p.read_text() and "apiVersion: apps/v1" in p.read_text() or "apiVersion: batch/v1" in p.read_text()]
    r = subprocess.run([tool("kubeconform"), "-strict", "-summary", *files], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr

def test_dcgm_field_names_exist_in_exporter_source():
    """Names used in alerts/dashboards must exist in dcgm-exporter. Set DCGM_EXPORTER_SRC to a clone to run."""
    import re
    src = os.environ.get("DCGM_EXPORTER_SRC")
    if not src or not Path(src).exists(): pytest.skip("DCGM_EXPORTER_SRC not set")
    real = set()
    for p in Path(src).rglob("*"):
        if p.is_file() and p.suffix in (".csv", ".go", ".md", ".yaml"): real |= set(re.findall(r"DCGM_FI_[A-Z0-9_]+", p.read_text(errors="ignore")))
    used = set()
    for p in list(HERE.glob("*.yaml")) + list(HERE.glob("*.json")): used |= set(re.findall(r"DCGM_FI_[A-Z0-9_]+", p.read_text()))
    assert used - real - {"DCGM_FI_DEV_GPU_NEW_METRIC"} == set()
