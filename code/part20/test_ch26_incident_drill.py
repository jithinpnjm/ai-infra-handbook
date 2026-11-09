"""Tests for the stress-interview drill runner (chapter 20.26)."""
import json
import pathlib
import subprocess
import sys

import pytest

from ch26_model import load_incidents, validate_incident
from ch26_score import grade, scorecard
from ch26_session import Session

HERE = pathlib.Path(__file__).parent
INCIDENTS = load_incidents()


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def play(inc_id, steps, minutes=30):
    clock = Clock()
    s = Session(INCIDENTS[inc_id], minutes, clock)
    for secs, line in steps:
        clock.t = secs
        s.handle(line)
    return s, clock


def test_ten_incidents_five_each():
    assert len(INCIDENTS) == 10
    kinds = [i["kind"] for i in INCIDENTS.values()]
    assert kinds.count("inference") == 5 and kinds.count("general") == 5


@pytest.mark.parametrize("inc_id", sorted(INCIDENTS))
def test_every_must_ask_key_is_reachable_by_its_own_name(inc_id):
    s = Session(INCIDENTS[inc_id])
    for q in INCIDENTS[inc_id]["questions"]:
        assert s.handle(q["key"]) == q["answer"]
    assert set(s.revealed) == {q["key"] for q in INCIDENTS[inc_id]["questions"]}


def test_free_text_question_is_matched():
    s = Session(INCIDENTS["ttft-after-deploy"])
    assert "prefix_cache_hits" in s.handle("What is the prefix cache hit rate?")
    assert "Request rate" in s.handle("show me the dashboard")


def test_unknown_question_gets_no_answer_and_reveals_nothing():
    s = Session(INCIDENTS["ttft-after-deploy"])
    assert "do not have" in s.handle("what is the weather")
    assert s.revealed == []


def test_short_keywords_need_whole_words():
    s = Session(INCIDENTS["disk-full-node"])
    assert s.match_question("the audio was durable") is None
    assert s.match_question("run du on /var")["key"] == "du"


def test_validation_rejects_bad_points_and_missing_core_question():
    bad = json.loads(json.dumps(INCIDENTS["bad-config-push"]))
    bad["mitigations"][0]["points"] += 1
    with pytest.raises(ValueError):
        validate_incident(bad)
    bad = json.loads(json.dumps(INCIDENTS["bad-config-push"]))
    bad["questions"] = [q for q in bad["questions"] if q["key"] != "change"]
    with pytest.raises(ValueError):
        validate_incident(bad)


STRONG = [
    (10, "/sev 2"), (15, "/roles I am incident commander, Sam is ops, Lee posts comms"),
    (25, "what is the impact"), (35, "show me the dashboard"), (50, "what changed, any deploy"),
    (60, "/hyp the deploy changed routing"), (70, "what is the prefix cache hit rate"),
    (80, "show the waiting queue"), (90, "/hyp prefix cache hit rate collapsed"),
    (100, "/do roll back the deploy with rollout undo"), (110, "/status impact is p99 TTFT, rolling back"),
    (400, "/status rollback done, TTFT recovering"), (700, "/do verify the hit rate recovers"),
    (900, "/status recovered, writing the postmortem"), (1000, "/cause the router lost prefix routing"),
    (1100, "/done"),
]


def test_strong_run_scores_high():
    s, _ = play("ttft-after-deploy", STRONG)
    rows, total = scorecard(s)
    assert total >= 85 and grade(total) == "strong"
    assert dict(rows)["Safety"][0] == 10


def test_acting_before_asking_and_naming_cause_early_loses_points():
    steps = [(5, "/cause it is probably the cache"), (20, "/do restart all pods"), (30, "/done")]
    s, _ = play("ttft-after-deploy", steps)
    rows, total = scorecard(s)
    parts = dict(rows)
    assert parts["Take control (first 2 min)"][0] == 0
    assert parts["Mitigate before root cause"][0] == 0
    assert parts["Safety"][0] == 5
    assert total < 30


def test_late_severity_gets_no_control_points():
    steps = [(300, "/sev 1"), (310, "/roles me"), (320, "/done")]
    s, _ = play("ttft-after-deploy", steps)
    assert dict(scorecard(s)[0])["Take control (first 2 min)"][0] == 0


def test_status_cadence_expects_updates_in_a_long_session():
    s, clock = play("ttft-after-deploy", [(10, "/status first update")])
    clock.t = 1500
    assert dict(scorecard(s)[0])["Status cadence"][0] < 10


def test_hint_costs_points_and_time_limit_stops_input():
    s, clock = play("ttft-after-deploy", [(1, "/hint")])
    assert s.hints == 1
    clock.t = 5000
    assert "Time is up" in s.handle("what changed")
    assert s.finished


def test_destructive_per_incident_examples():
    s, _ = play("regional-partial-outage-retries", [(10, "/do fail over to the US region")])
    assert dict(scorecard(s)[0])["Safety"][0] == 5
    s, _ = play("etcd-latency", [(10, "/do defrag the slow member")])
    assert dict(scorecard(s)[0])["Safety"][0] == 5


def test_cli_list_and_replay(tmp_path):
    script = tmp_path / "s.txt"
    script.write_text("\n".join("%d|%s" % (t, line) for t, line in STRONG))
    cli = HERE / "ch26_incident_drill.py"
    out = subprocess.run([sys.executable, str(cli), "list"], capture_output=True, text=True, cwd=HERE)
    assert out.returncode == 0 and out.stdout.count("\n") == 10
    out = subprocess.run([sys.executable, str(cli), "replay", "ttft-after-deploy", str(script)],
                         capture_output=True, text=True, cwd=HERE)
    assert "Total:" in out.stdout and "(strong)" in out.stdout


@pytest.mark.parametrize("inc_id", sorted(INCIDENTS))
def test_a_model_answer_built_from_the_definition_scores_strong(inc_id):
    inc = INCIDENTS[inc_id]
    steps = [(10, "/sev 2"), (20, "/roles ic, ops, comms")]
    steps += [(30 + i, k) for i, k in enumerate(inc["must_ask"])]
    steps += [(60, "/hyp " + inc["likely_first"][0]), (70, "/hyp " + inc["root_cause_keywords"][0])]
    steps += [(100 + i, "/do " + m["any"][0]) for i, m in enumerate(inc["mitigations"])]
    steps += [(200, "/status impact and plan"), (800, "/status mitigated"), (1400, "/status stable"),
              (1500, "/cause " + inc["root_cause"])]
    s, _ = play(inc_id, steps)
    assert scorecard(s)[1] >= 85
