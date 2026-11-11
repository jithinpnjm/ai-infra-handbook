"""PoC tracker for chapter 19.10.

Reads success and exit criteria (agreed before the PoC) and a results file,
and prints a go or no-go. Standard library only.

Verdict order, first match wins:
  STOP          an exit criterion is true
  NO-GO         a "must" criterion was measured often enough and failed
  INCONCLUSIVE  a "must" criterion is missing or has too few runs
  GO WITH CONDITIONS  all musts pass, a "should" fails or is not measured
  GO            everything passes

    python3 c10_poc_tracker.py c10_poc_criteria.json c10_poc_results_larkfield.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXIT_CODES = {"GO": 0, "GO WITH CONDITIONS": 0, "NO-GO": 1, "INCONCLUSIVE": 2, "STOP": 3}
_OPS = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b, "<": lambda a, b: a < b}


def validate_criteria(doc: dict) -> None:
    ids = set()
    for kind in ("success", "exit"):
        for c in doc.get(kind, []):
            if c["id"] in ids:
                raise ValueError(f"duplicate criterion id {c['id']}")
            ids.add(c["id"])
            if c["op"] not in _OPS:
                raise ValueError(f"{c['id']}: unsupported operator {c['op']!r}")
            if not isinstance(c["threshold"], (int, float)) or isinstance(c["threshold"], bool):
                raise ValueError(f"{c['id']}: threshold must be a number")
    if not doc.get("success"):
        raise ValueError("a PoC needs at least one success criterion")
    if not any(c["priority"] == "must" for c in doc["success"]):
        raise ValueError("a PoC needs at least one 'must' criterion")
    for c in doc["success"]:
        if c["priority"] not in ("must", "should"):
            raise ValueError(f"{c['id']}: priority must be 'must' or 'should'")


def _reading(results: dict, metric: str):
    m = results.get("metrics", {}).get(metric)
    if m is None:
        return None
    v, runs = m.get("value"), m.get("runs", 0)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{metric}: value must be a number, got {v!r}")
    return v, runs


def evaluate(criteria: dict, results: dict) -> dict:
    validate_criteria(criteria)
    rows, stops, unmonitored = [], [], []
    for c in criteria.get("exit", []):
        r = _reading(results, c["metric"])
        if r is None:
            unmonitored.append(c["id"])
        elif _OPS[c["op"]](r[0], c["threshold"]):
            stops.append({"id": c["id"], "value": r[0], "action": c["action"]})
    for c in criteria["success"]:
        r = _reading(results, c["metric"])
        if r is None:
            status, value, runs = "missing", None, 0
        else:
            value, runs = r
            if runs < c.get("min_runs", 1):
                status = "too_few_runs"
            else:
                status = "pass" if _OPS[c["op"]](value, c["threshold"]) else "fail"
        rows.append({"id": c["id"], "metric": c["metric"], "priority": c["priority"], "op": c["op"],
                     "threshold": c["threshold"], "value": value, "runs": runs,
                     "min_runs": c.get("min_runs", 1), "status": status})
    musts = [r for r in rows if r["priority"] == "must"]
    shoulds = [r for r in rows if r["priority"] == "should"]
    if stops:
        verdict = "STOP"
    elif any(r["status"] == "fail" for r in musts):
        verdict = "NO-GO"
    elif any(r["status"] in ("missing", "too_few_runs") for r in musts):
        verdict = "INCONCLUSIVE"
    elif any(r["status"] != "pass" for r in shoulds):
        verdict = "GO WITH CONDITIONS"
    else:
        verdict = "GO"
    return {"verdict": verdict, "criteria": rows, "stops": stops, "unmonitored_exit": unmonitored,
            "exit_code": EXIT_CODES[verdict]}


def render(report: dict) -> str:
    lines = []
    for r in report["criteria"]:
        got = "-" if r["value"] is None else r["value"]
        lines.append(f"  {r['id']} {r['priority']:<6} {r['metric']:<24} {got} {r['op']} {r['threshold']}"
                     f"  runs {r['runs']}/{r['min_runs']}  {r['status'].upper()}")
    for s in report["stops"]:
        lines.append(f"  EXIT {s['id']} value {s['value']}: {s['action']}")
    if report["unmonitored_exit"]:
        lines.append("  Exit criteria with no reading: " + ", ".join(report["unmonitored_exit"]))
    lines.append(f"VERDICT: {report['verdict']}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: c10_poc_tracker.py criteria.json results.json", file=sys.stderr)
        return 2
    try:
        report = evaluate(json.loads(Path(argv[1]).read_text()), json.loads(Path(argv[2]).read_text()))
    except (ValueError, KeyError) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    print(render(report))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
