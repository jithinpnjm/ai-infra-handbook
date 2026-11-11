"""Tests for the chapter 19.10 consulting-method tools: discovery scorer,
assessment scorecard, PoC tracker and ADR generator."""
import copy
import json
from pathlib import Path

import pytest

import c10_adr as adr
import c10_discovery as disc
import c10_engagement_demo as demo
import c10_poc_tracker as poc
import c10_scorecard as sc

HERE = Path(__file__).resolve().parent


def jl(name):
    return json.loads((HERE / name).read_text())


@pytest.fixture
def q():
    return disc.load_questionnaire()


@pytest.fixture
def answers():
    return jl("c10_answers_larkfield.json")


# ---- discovery ----
def test_questionnaire_covers_all_areas(q):
    assert {x["area"] for x in q["questions"]} == set(q["areas"])
    assert len(q["questions"]) == 29


def test_larkfield_flags_and_completeness(q, answers):
    r = disc.score(q, answers)
    assert [f["id"] for f in r["flags"]] == ["R05", "R07", "R09", "R03"]
    assert r["completeness"] == pytest.approx(0.956, abs=0.001)
    assert r["ready_for_assessment"] is True
    assert r["unanswered"] == ["bud.commitments", "tl.deadline_reason"]


def test_unknown_critical_blocks_readiness(q, answers):
    answers["dat.quality_known"] = "unknown"
    r = disc.score(q, answers)
    assert r["ready_for_assessment"] is False
    assert "UNKNOWN:dat.quality_known" in [f["id"] for f in r["flags"]]
    assert r["flags"][0]["severity"] == "high"


def test_empty_answers_are_not_ready(q):
    r = disc.score(q, {})
    assert r["completeness"] == 0 and not r["ready_for_assessment"]
    assert len(r["critical_unanswered"]) == sum(x["critical"] for x in q["questions"])


def test_residency_conflict_rule(q, answers):
    answers["wl.model_source"] = "hosted_api"
    assert "R04" in [f["id"] for f in disc.score(q, answers)["flags"]]


def test_cross_question_rule_approval_vs_pilot(q, answers):
    answers["cmp.approval_weeks"] = 20
    assert "R10" in [f["id"] for f in disc.score(q, answers)["flags"]]
    answers["cmp.approval_weeks"] = 16  # equal is not greater
    assert "R10" not in [f["id"] for f in disc.score(q, answers)["flags"]]


@pytest.mark.parametrize("bad", [
    {"nope.id": 1},
    {"wl.peak_concurrent": "forty"},
    {"wl.peak_concurrent": True},
    {"wl.interaction": "sometimes"},
    {"stk.decision_maker": "yes"},
    {"wl.use_case": "  "},
])
def test_invalid_answers_rejected(q, bad):
    with pytest.raises(ValueError):
        disc.score(q, bad)


def test_bad_questionnaire_rejected(tmp_path, q):
    broken = copy.deepcopy(q)
    broken["risk_rules"][0]["all"][0]["q"] = "missing.id"
    p = tmp_path / "q.json"
    p.write_text(json.dumps(broken))
    with pytest.raises(ValueError):
        disc.load_questionnaire(p)


def test_discovery_cli_exit_codes(tmp_path):
    good = HERE / "c10_answers_larkfield.json"
    assert disc.main(["x", str(good)]) == 0
    bad = tmp_path / "a.json"
    bad.write_text('{"nope": 1}')
    assert disc.main(["x", str(bad)]) == 2
    empty = tmp_path / "e.json"
    empty.write_text("{}")
    assert disc.main(["x", str(empty)]) == 1


# ---- scorecard ----
def test_scorecard_larkfield():
    p = jl("c10_scores_larkfield.json")
    r = sc.evaluate(sc.load_scorecard(), p["scores"], p["targets"])
    assert r["assessment_complete"]
    assert r["categories"]["mlops"]["maturity"] == 0.70
    assert r["categories"]["security"]["maturity"] == 2.38
    assert [g["id"] for g in r["gaps"][:3]] == ["ml.evaluation", "tm.gpu_ops", "inf.gpu_inventory"]
    assert r["gaps"][0]["priority"] == 9


def test_scorecard_requires_evidence():
    with pytest.raises(ValueError, match="evidence"):
        sc.evaluate(sc.load_scorecard(), {"tm.k8s": {"score": 2, "evidence": " "}})


@pytest.mark.parametrize("score", [4, -1, 1.5, True, "2"])
def test_scorecard_rejects_bad_scores(score):
    with pytest.raises(ValueError):
        sc.evaluate(sc.load_scorecard(), {"tm.k8s": {"score": score, "evidence": "x"}})


def test_scorecard_unknown_criterion_and_partial():
    with pytest.raises(ValueError):
        sc.evaluate(sc.load_scorecard(), {"zzz": {"score": 1, "evidence": "x"}})
    r = sc.evaluate(sc.load_scorecard(), {"tm.k8s": {"score": 2, "evidence": "ok"}})
    assert not r["assessment_complete"]
    assert r["categories"]["team"]["complete"] is False
    assert "tm.gpu_ops" in r["not_assessed"]


# ---- PoC tracker ----
@pytest.fixture
def crit():
    return jl("c10_poc_criteria.json")


@pytest.fixture
def res():
    return jl("c10_poc_results_larkfield.json")


def test_poc_go_with_conditions(crit, res):
    r = poc.evaluate(crit, res)
    assert r["verdict"] == "GO WITH CONDITIONS" and r["exit_code"] == 0


def test_poc_go_when_all_pass(crit, res):
    res["metrics"]["cost_per_1000_requests"]["value"] = 1.5
    assert poc.evaluate(crit, res)["verdict"] == "GO"


def test_poc_no_go_when_must_fails(crit, res):
    res["metrics"]["p95_latency_s"]["value"] = 9.4
    r = poc.evaluate(crit, res)
    assert r["verdict"] == "NO-GO" and r["exit_code"] == 1


def test_poc_boundary_value_passes(crit, res):
    res["metrics"]["p95_latency_s"]["value"] = 8
    assert poc.evaluate(crit, res)["verdict"] == "GO WITH CONDITIONS"


def test_poc_too_few_runs_is_inconclusive_not_pass(crit, res):
    res["metrics"]["p95_latency_s"]["runs"] = 2
    assert poc.evaluate(crit, res)["verdict"] == "INCONCLUSIVE"


def test_poc_missing_must_is_inconclusive(crit, res):
    del res["metrics"]["unsupported_claim_rate"]
    assert poc.evaluate(crit, res)["verdict"] == "INCONCLUSIVE"


def test_poc_exit_beats_everything(crit, res):
    res["metrics"]["gpu_hours_used"]["value"] = 1300
    r = poc.evaluate(crit, res)
    assert r["verdict"] == "STOP" and r["exit_code"] == 3
    res["metrics"]["p95_latency_s"]["value"] = 99  # still STOP, not NO-GO
    assert poc.evaluate(crit, res)["verdict"] == "STOP"


def test_poc_unmonitored_exit_is_reported(crit, res):
    del res["metrics"]["security_blockers_open"]
    r = poc.evaluate(crit, res)
    assert r["unmonitored_exit"] == ["X3"]


def test_poc_should_missing_means_conditions(crit, res):
    res["metrics"]["cost_per_1000_requests"]["value"] = 1.0
    del res["metrics"]["adjuster_minutes_saved"]
    assert poc.evaluate(crit, res)["verdict"] == "GO WITH CONDITIONS"


def test_poc_bad_inputs(crit, res):
    bad = copy.deepcopy(crit)
    bad["success"][0]["op"] = "=="
    with pytest.raises(ValueError):
        poc.evaluate(bad, res)
    bad = copy.deepcopy(crit)
    bad["success"] = [c for c in bad["success"] if c["priority"] != "must"]
    with pytest.raises(ValueError, match="must"):
        poc.evaluate(bad, res)
    res["metrics"]["p95_latency_s"]["value"] = "fast"
    with pytest.raises(ValueError):
        poc.evaluate(crit, res)


def test_poc_cli(tmp_path):
    a, b = HERE / "c10_poc_criteria.json", HERE / "c10_poc_results_larkfield.json"
    assert poc.main(["x", str(a), str(b)]) == 0
    assert poc.main(["x", str(a)]) == 2


# ---- ADR ----
@pytest.fixture
def d():
    return {k: v for k, v in jl("c10_adr_input_larkfield.json").items() if not k.startswith("_")}


def test_adr_renders_sections(d):
    text = adr.render(d, 7)
    assert text.startswith("# ADR 0007:")
    for h in ("## Context", "## Options considered", "## Decision", "## Consequences", "## Revisit when"):
        assert h in text
    assert text.count("(chosen)") == 1


def test_adr_numbering_and_write(d, tmp_path):
    p1 = adr.write(d, tmp_path)
    p2 = adr.write(d, tmp_path)
    assert p1.name.startswith("0001-") and p2.name.startswith("0002-")


def test_adr_refuses_one_sided_or_unnamed_decision(d):
    bad = copy.deepcopy(d)
    bad["options"][0]["cons"] = []
    with pytest.raises(ValueError, match="cons"):
        adr.render(bad, 1)
    bad = copy.deepcopy(d)
    bad["decision"] = "Something else"
    with pytest.raises(ValueError, match="not one of"):
        adr.render(bad, 1)
    bad = copy.deepcopy(d)
    bad["options"] = bad["options"][:1]
    with pytest.raises(ValueError, match="two options"):
        adr.render(bad, 1)
    bad = copy.deepcopy(d)
    bad["revisit_when"] = []
    with pytest.raises(ValueError, match="revisit"):
        adr.render(bad, 1)
    bad = copy.deepcopy(d)
    bad["date"] = "10/11/2026"
    with pytest.raises(ValueError, match="date"):
        adr.render(bad, 1)


def test_demo_runs_end_to_end():
    r = demo.run()
    assert r["poc"]["verdict"] == "GO WITH CONDITIONS"
    assert r["discovery"]["ready_for_assessment"]
    assert "ADR 0001" in r["adr"]
