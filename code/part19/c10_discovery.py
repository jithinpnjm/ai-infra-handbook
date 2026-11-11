"""Discovery questionnaire scorer for chapter 19.10.

The questionnaire is data (c10_questionnaire.json). This module loads it,
validates a customer's answers, and reports completeness and risk flags.
Standard library only.

    python3 c10_discovery.py c10_answers_larkfield.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNKNOWN = "unknown"
SEVERITY_ORDER = {"high": 0, "medium": 1, "info": 2}
CRITICAL_WEIGHT = 2
NORMAL_WEIGHT = 1
READY_COMPLETENESS = 0.80  # author's heuristic, not a published threshold


def load_questionnaire(path: str | Path | None = None) -> dict:
    path = Path(path) if path else HERE / "c10_questionnaire.json"
    doc = json.loads(path.read_text())
    ids = [q["id"] for q in doc["questions"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate question id in questionnaire")
    for q in doc["questions"]:
        if q["area"] not in doc["areas"]:
            raise ValueError(f"{q['id']}: unknown area {q['area']}")
        if q["type"] == "choice" and not q.get("options"):
            raise ValueError(f"{q['id']}: choice question without options")
    for rule in doc["risk_rules"]:
        for cond in rule["all"]:
            for ref in (cond["q"], cond.get("value_q")):
                if ref is not None and ref not in ids:
                    raise ValueError(f"rule {rule['id']} refers to unknown question {ref}")
    return doc


def strip_notes(answers: dict) -> dict:
    """Keys that start with an underscore are comments, not answers."""
    return {k: v for k, v in answers.items() if not k.startswith("_")}


def validate_answers(doc: dict, answers: dict) -> None:
    """Raise ValueError on an unknown id, a wrong type or a bad choice."""
    answers = strip_notes(answers)
    by_id = {q["id"]: q for q in doc["questions"]}
    for qid, value in answers.items():
        if qid not in by_id:
            raise ValueError(f"unknown question id: {qid}")
        if value == UNKNOWN or value is None:
            continue
        q = by_id[qid]
        kind = q["type"]
        if kind == "bool" and not isinstance(value, bool):
            raise ValueError(f"{qid}: expected true or false, got {value!r}")
        if kind == "number" and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise ValueError(f"{qid}: expected a number, got {value!r}")
        if kind == "choice" and value not in q["options"]:
            raise ValueError(f"{qid}: {value!r} is not one of {q['options']}")
        if kind == "text" and not (isinstance(value, str) and value.strip()):
            raise ValueError(f"{qid}: expected non-empty text")


def is_answered(answers: dict, qid: str) -> bool:
    return qid in answers and answers[qid] is not None and answers[qid] != UNKNOWN


_OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
}


def _cond_true(cond: dict, answers: dict) -> bool:
    if not is_answered(answers, cond["q"]):
        return False  # an unanswered question cannot fire a rule; unknowns are reported separately
    left = answers[cond["q"]]
    if "value_q" in cond:
        if not is_answered(answers, cond["value_q"]):
            return False
        right = answers[cond["value_q"]]
    else:
        right = cond["value"]
    return _OPS[cond["op"]](left, right)


def score(doc: dict, answers: dict) -> dict:
    answers = strip_notes(answers)
    validate_answers(doc, answers)
    qs = doc["questions"]
    total_w = sum(CRITICAL_WEIGHT if q["critical"] else NORMAL_WEIGHT for q in qs)
    got_w = 0
    per_area: dict[str, dict] = {a: {"answered": 0, "total": 0} for a in doc["areas"]}
    unanswered, critical_unanswered = [], []
    for q in qs:
        per_area[q["area"]]["total"] += 1
        if is_answered(answers, q["id"]):
            per_area[q["area"]]["answered"] += 1
            got_w += CRITICAL_WEIGHT if q["critical"] else NORMAL_WEIGHT
        else:
            unanswered.append(q["id"])
            if q["critical"]:
                critical_unanswered.append(q["id"])
    flags = []
    for rule in doc["risk_rules"]:
        if all(_cond_true(c, answers) for c in rule["all"]):
            flags.append({"id": rule["id"], "severity": rule["severity"], "message": rule["message"]})
    for qid in critical_unanswered:
        flags.append({"id": f"UNKNOWN:{qid}", "severity": "high",
                      "message": f"Critical question {qid} is unanswered or unknown."})
    flags.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["id"]))
    completeness = got_w / total_w
    return {
        "completeness": round(completeness, 3),
        "per_area": per_area,
        "unanswered": unanswered,
        "critical_unanswered": critical_unanswered,
        "flags": flags,
        "ready_for_assessment": completeness >= READY_COMPLETENESS and not critical_unanswered,
    }


def render(report: dict) -> str:
    lines = [f"Completeness (weighted): {report['completeness']:.1%}"]
    for area, c in report["per_area"].items():
        lines.append(f"  {area:<13} {c['answered']}/{c['total']}")
    lines.append(f"Ready for assessment: {'yes' if report['ready_for_assessment'] else 'no'}")
    lines.append("Risk flags:")
    if not report["flags"]:
        lines.append("  none")
    for f in report["flags"]:
        lines.append(f"  [{f['severity']:<6}] {f['id']}: {f['message']}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: c10_discovery.py answers.json [questionnaire.json]", file=sys.stderr)
        return 2
    doc = load_questionnaire(argv[2] if len(argv) > 2 else None)
    try:
        report = score(doc, json.loads(Path(argv[1]).read_text()))
    except ValueError as exc:
        print(f"invalid answers: {exc}", file=sys.stderr)
        return 2
    print(render(report))
    return 0 if report["ready_for_assessment"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
