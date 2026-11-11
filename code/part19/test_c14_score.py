import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import c14_bank  # noqa: E402
import c14_score as s  # noqa: E402

D0 = dt.date(2026, 1, 1)


@pytest.fixture(scope="module")
def bank():
    return c14_bank.load_bank()


def test_good_grades_climb_boxes_with_growing_gaps():
    st = s.new_state()
    gaps = []
    d = D0
    for _ in range(6):
        c = s.record(st, "X", 3, d)
        gaps.append((dt.date.fromisoformat(c["due"]) - d).days)
        d = dt.date.fromisoformat(c["due"])
    assert gaps == [2, 4, 8, 16, 16, 16]
    assert c["box"] == 5


def test_weak_grade_resets_to_box_one():
    st = s.new_state()
    s.record(st, "X", 3, D0)
    s.record(st, "X", 2, D0)
    c = s.record(st, "X", 1, D0)
    assert c["box"] == 1 and c["due"] == (D0 + dt.timedelta(days=1)).isoformat()


def test_invalid_grade_rejected():
    with pytest.raises(ValueError):
        s.record(s.new_state(), "X", 4, D0)


def test_due_order_scheduled_first_then_unseen(bank):
    st = s.new_state()
    a, b = bank["questions"][0]["id"], bank["questions"][1]["id"]
    s.record(st, a, 3, D0)       # due D0+2
    s.record(st, b, 0, D0)       # due D0+1
    assert s.due_ids(st, bank, D0)[0] not in (a, b)           # nothing due yet, unseen first
    ids = s.due_ids(st, bank, D0 + dt.timedelta(days=2))
    assert ids[:2] == [b, a]
    assert len(ids) == len(bank["questions"])


def test_score_rolls_up_by_topic_and_level(bank):
    st = s.new_state()
    q = bank["questions"]
    first_linux = next(x for x in q if x["topic"] == "linux")
    first_net = next(x for x in q if x["topic"] == "networking")
    s.record(st, first_linux["id"], 3, D0)
    s.record(st, first_net["id"], 1, D0)
    rep = s.score(bank, st)
    assert rep["by_topic"]["linux"]["percent"] == 100.0
    assert rep["by_topic"]["networking"]["percent"] == pytest.approx(33.3, abs=0.1)
    assert rep["overall_percent"] == pytest.approx(66.7, abs=0.1)
    assert s.weakest_topics(rep, 1) == ["networking"]


def test_latest_grade_counts(bank):
    st = s.new_state()
    qid = bank["questions"][0]["id"]
    s.record(st, qid, 0, D0)
    s.record(st, qid, 3, D0)
    assert s.score(bank, st)["overall_percent"] == 100.0


def test_state_round_trip(tmp_path):
    st = s.new_state()
    s.record(st, "X", 2, D0)
    p = tmp_path / "st.json"
    s.save_state(st, p)
    assert s.load_state(p) == st
    assert s.load_state(tmp_path / "none.json") == s.new_state()


def test_scripted_quiz_session(bank):
    st = s.new_state()
    ids = [q["id"] for q in bank["questions"][:3]]
    answers = iter(["", "x", "3", "", "2", "", "q"])   # invalid grade "x" is re-asked
    out = []
    done = s.run_quiz(bank, st, ids, ask=lambda _p: next(answers), out=out.append, today=D0)
    assert done == 2
    assert set(st["cards"]) == set(ids[:2])
    assert any("Please enter" in line for line in out)
    assert any("Follow-up:" in line for line in out)


def test_cli_report_and_quiz(tmp_path, monkeypatch, capsys):
    stp = tmp_path / "s.json"
    feed = iter(["", "3", "", "q"])
    monkeypatch.setattr("builtins.input", lambda _p="": next(feed))
    assert s.main(["--state", str(stp), "--n", "2", "--topic", "linux", "--seed", "1"]) == 0
    assert stp.is_file()
    assert s.main(["--state", str(stp), "--report"]) == 0
    assert "Weakest topics" in capsys.readouterr().out
