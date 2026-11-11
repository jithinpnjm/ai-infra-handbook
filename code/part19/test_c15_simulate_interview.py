import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import c15_simulate_interview as sim  # noqa: E402

Q = sim.Question("t1", "kubernetes", "Pod Pending?", [["events", "describe"], ["taint"], ["allocatable"]], "20.23")
GOOD = ("I would assume a GPU pod and first read the events with describe. Then node allocatable shows 8 GB "
        "free, but a taint instead of a toleration can block it.")


def test_builtin_bank_when_no_file(tmp_path):
    qs, src = sim.load_bank(str(tmp_path / "missing.json"))
    assert src == "built-in" and len(qs) >= 10
    assert all(q.key_points for q in qs)


def test_bank_file_is_used_when_present(tmp_path):
    p = tmp_path / "bank.json"
    p.write_text(json.dumps({"questions": [{"id": "x", "question": "Why?", "topic": "gpu", "key_points": ["nvlink"]}]}))
    qs, src = sim.load_bank(str(p))
    assert src == "bank:bank.json" and qs[0].id == "x" and qs[0].key_points == [["nvlink"]]


def test_unusable_bank_falls_back(tmp_path):
    p = tmp_path / "bank.json"
    p.write_text("{not json")
    assert sim.load_bank(str(p))[1] == "built-in"


def test_draw_is_seeded_and_filters_topic():
    qs, _ = sim.load_bank("/nonexistent")
    assert [q.id for q in sim.draw(qs, 4, seed=7)] == [q.id for q in sim.draw(qs, 4, seed=7)]
    assert all(q.topic == "training" for q in sim.draw(qs, 5, seed=1, topic="training"))
    with pytest.raises(ValueError):
        sim.draw(qs, 1, topic="nope")


def test_good_answer_scores_high_and_empty_scores_zero():
    good = sim.score_answer(Q, GOOD, 60, 120)
    assert good.total == 100 and not good.missed
    empty = sim.score_answer(Q, "  ", 10, 120)
    assert empty.total == 20 and "empty answer" in empty.notes  # only the time points remain


def test_missing_points_are_named():
    s = sim.score_answer(Q, "Check the events.", 30, 120)
    assert s.missed == ["taint", "allocatable"]
    assert s.coverage == pytest.approx(50 / 3)


def test_over_time_is_penalised_in_two_steps():
    on = sim.score_answer(Q, GOOD, 120, 120).total
    over = sim.score_answer(Q, GOOD, 150, 120).total
    far = sim.score_answer(Q, GOOD, 200, 120).total
    assert on - over == 10 and over - far == 10 and "far over time" in sim.score_answer(Q, GOOD, 200, 120).notes


def test_question_without_key_points_is_flagged():
    s = sim.score_answer(sim.Question("n", "x", "?", []), "I assume 5 s", 10, 120)
    assert any("not scored" in n for n in s.notes)


def test_session_log_and_clock(tmp_path):
    ticks = iter([0, 50, 100, 300])  # round 1 takes 50 s, round 2 takes 200 s
    log = tmp_path / "log.jsonl"
    qs = [Q, sim.Question("t2", "gpu", "MIG?", [["profile"]], "19.8")]
    out = []
    session = sim.run_session(qs, lambda q: GOOD, 120, clock=lambda: next(ticks), log_path=str(log), out=out.append)
    rec = json.loads(log.read_text().splitlines()[0])
    assert rec["rounds"][0]["elapsed_s"] == 50 and rec["rounds"][1]["elapsed_s"] == 200
    assert "far over time" in rec["rounds"][1]["notes"]
    assert session["mean"] == rec["mean"]


def test_cli_non_interactive(tmp_path, capsys):
    ans = tmp_path / "a.json"
    ans.write_text(json.dumps({"b04": GOOD}))
    log = tmp_path / "l.jsonl"
    rc = sim.main(["--rounds", "1", "--topic", "kubernetes", "--seed", "1", "--answers", str(ans),
                   "--log", str(log), "--bank", "/nonexistent"])
    assert rc == 0 and log.exists()
    assert "Question source: built-in" in capsys.readouterr().out
