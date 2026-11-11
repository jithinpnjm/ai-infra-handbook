#!/usr/bin/env python3
"""Quiz runner, self-assessment scorer and spaced-repetition scheduler for the 19.14 bank.

Self-assessment scale (you grade yourself after reading the model answer):
  0 = blank, 1 = weak (matches the weak answer), 2 = good, 3 = strong (covers every point)
Leitner boxes: a grade of 2 or 3 moves a question up one box, a grade of 0 or 1 sends it
back to box 1. Review gaps in days per box: 1, 2, 4, 8, 16.
State is a JSON file you keep between sessions.

Run: python3 c14_score.py --state mystate.json --n 5 [--topic linux] [--level core]
     python3 c14_score.py --state mystate.json --report
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import sys
from collections import defaultdict

import c14_bank

GRADES = (0, 1, 2, 3)
INTERVALS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
MAX_BOX = 5


def new_state() -> dict:
    return {"cards": {}}


def load_state(path) -> dict:
    p = pathlib.Path(path)
    return json.loads(p.read_text()) if p.is_file() else new_state()


def save_state(state: dict, path) -> None:
    pathlib.Path(path).write_text(json.dumps(state, indent=1, sort_keys=True))


def record(state: dict, qid: str, grade: int, today: dt.date) -> dict:
    """Apply one self-assessed grade and schedule the next review."""
    if grade not in GRADES:
        raise ValueError(f"grade must be one of {GRADES}, got {grade!r}")
    card = state["cards"].setdefault(qid, {"box": 1, "due": today.isoformat(), "history": []})
    card["box"] = min(card["box"] + 1, MAX_BOX) if grade >= 2 else 1
    card["due"] = (today + dt.timedelta(days=INTERVALS[card["box"]])).isoformat()
    card["history"].append([today.isoformat(), grade])
    return card


def due_ids(state: dict, bank: dict, today: dt.date) -> list[str]:
    """Question ids due today: scheduled cards first (oldest due first), then unseen ones."""
    seen_due = sorted(
        (c["due"], qid) for qid, c in state["cards"].items() if c["due"] <= today.isoformat()
    )
    ordered = [qid for _, qid in seen_due]
    unseen = [q["id"] for q in bank["questions"] if q["id"] not in state["cards"]]
    return ordered + unseen


def score(bank: dict, state: dict) -> dict:
    """Latest grade per question rolled up by topic and by level, as a percent of the maximum 3."""
    by_id = {q["id"]: q for q in bank["questions"]}
    topic = defaultdict(list)
    level = defaultdict(list)
    for qid, card in state["cards"].items():
        if qid not in by_id or not card["history"]:
            continue
        g = card["history"][-1][1]
        topic[by_id[qid]["topic"]].append(g)
        level[by_id[qid]["difficulty"]].append(g)

    def pct(vals):
        return round(100.0 * sum(vals) / (3 * len(vals)), 1) if vals else None

    return {
        "answered": sum(len(v) for v in topic.values()),
        "by_topic": {k: {"n": len(v), "percent": pct(v)} for k, v in sorted(topic.items())},
        "by_level": {k: {"n": len(v), "percent": pct(v)} for k, v in sorted(level.items())},
        "overall_percent": pct([g for v in topic.values() for g in v]),
    }


def weakest_topics(report: dict, limit: int = 3) -> list[str]:
    rows = [(v["percent"], k) for k, v in report["by_topic"].items() if v["percent"] is not None]
    return [k for _, k in sorted(rows)[:limit]]


def run_quiz(bank, state, ids, ask=None, out=print, today=None) -> int:
    """Interactive loop. `ask` and `out` are injectable so tests can script a session."""
    ask = ask or (lambda prompt: input(prompt))
    today = today or dt.date.today()
    by_id = {q["id"]: q for q in bank["questions"]}
    done = 0
    for qid in ids:
        q = by_id[qid]
        out(f"\n[{q['id']}] ({q['topic']}, {q['difficulty']})\n{q['question']}")
        ask("Answer out loud, then press Enter to see the model answer. ")
        out(f"\nModel answer: {q['model_answer']}")
        out("A strong answer contains: " + "; ".join(q["strong_answer_contains"]))
        out(f"A common weak answer: {q['weak_answer']}")
        out(f"Follow-up: {q['follow_up']}")
        out(f"Chapter: {q['link']}")
        while True:
            raw = ask("Grade yourself 0 blank, 1 weak, 2 good, 3 strong (q to stop): ").strip().lower()
            if raw == "q":
                return done
            if raw.isdigit() and int(raw) in GRADES:
                record(state, qid, int(raw), today)
                done += 1
                break
            out("Please enter 0, 1, 2, 3 or q.")
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", default=str(c14_bank.DEFAULT_BANK))
    ap.add_argument("--state", default="c14_state.json")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--topic")
    ap.add_argument("--level", choices=c14_bank.LEVELS)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    bank = c14_bank.load_bank(a.bank)
    state = load_state(a.state)
    if a.report:
        rep = score(bank, state)
        print(json.dumps(rep, indent=1))
        print("Weakest topics:", ", ".join(weakest_topics(rep)) or "none yet")
        return 0
    ids = due_ids(state, bank, dt.date.today())
    by_id = {q["id"]: q for q in bank["questions"]}
    ids = [i for i in ids if (not a.topic or by_id[i]["topic"] == a.topic)
           and (not a.level or by_id[i]["difficulty"] == a.level)]
    if a.seed is not None:
        random.Random(a.seed).shuffle(ids)
    done = run_quiz(bank, state, ids[: a.n])
    save_state(state, a.state)
    print(f"\n{done} graded. State saved to {a.state}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
