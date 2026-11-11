#!/usr/bin/env python3
"""Walkthrough for chapter 19.15: validate the sheet, print the arithmetic, run one scripted mock round.

No GPU and no network. The mock answers are scripted so the output is repeatable.
Usage: c15_walkthrough.py
"""
from __future__ import annotations

import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c15_numbers as nums  # noqa: E402
import c15_sheet_validator as val  # noqa: E402
import c15_simulate_interview as sim  # noqa: E402

SCRIPT = {
    "b04": ("I would assume a GPU pod. First I read the events with describe. Then node allocatable "
            "shows 8 GPUs free, but a taint without a toleration can block it."),
    "b09": "Use burn rate alerts.",
    "b07": "Checkpoint every hour.",
}
CLOCK_STEPS = {"b04": 70, "b09": 20, "b07": 200}


def main() -> int:
    text = open(val.DEFAULT_SHEET, encoding="utf-8").read()
    rep = val.validate(text)
    print(f"Step 1. Sheet: {rep.rows} rows, {len(rep.problems)} problems")
    per = collections.Counter(r.section.split(".")[0] for r in val.parse_sheet(text))
    print("  rows per section:", ", ".join(f"{k}={v}" for k, v in sorted(per.items())))
    print("\nStep 2. Arithmetic the sheet quotes")
    for k, v in nums.table():
        print(f"  {k:42s} {v}")
    print("\nStep 3. Scripted mock round (built-in bank)")
    qs, source = sim.load_bank("/nonexistent")
    by_id = {q.id: q for q in qs}
    picked = [by_id[i] for i in SCRIPT]
    t = [0.0]
    cur = {}

    def answer(q):
        cur["q"] = q
        return SCRIPT[q.id]

    def clock():
        # called before and after each answer: advance by the scripted duration after it
        q = cur.get("q")
        if q is not None and cur.get("done") is not q:
            cur["done"] = q
            t[0] += CLOCK_STEPS[q.id]
        return t[0]

    sim.run_session(picked, answer, 120, clock=clock, source=source)
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
