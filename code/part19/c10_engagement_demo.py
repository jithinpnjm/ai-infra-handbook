"""Runs the fictional Larkfield engagement end to end: discovery, scorecard,
PoC verdict and ADR. Prints a one-page summary. Fictional data only."""
from __future__ import annotations

import json
from pathlib import Path

import c10_adr as adr
import c10_discovery as disc
import c10_poc_tracker as poc
import c10_scorecard as sc

HERE = Path(__file__).resolve().parent


def run() -> dict:
    j = lambda n: json.loads((HERE / n).read_text())
    d = disc.score(disc.load_questionnaire(), j("c10_answers_larkfield.json"))
    s = sc.evaluate(sc.load_scorecard(), j("c10_scores_larkfield.json")["scores"], j("c10_scores_larkfield.json")["targets"])
    p = poc.evaluate(j("c10_poc_criteria.json"), j("c10_poc_results_larkfield.json"))
    a = {k: v for k, v in j("c10_adr_input_larkfield.json").items() if not k.startswith("_")}
    return {"discovery": d, "scorecard": s, "poc": p, "adr": adr.render(a, 1)}


if __name__ == "__main__":
    r = run()
    print(disc.render(r["discovery"])); print()
    print(sc.render(r["scorecard"])); print()
    print(poc.render(r["poc"])); print()
    print(r["adr"])
