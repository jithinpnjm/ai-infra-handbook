#!/usr/bin/env python3
"""Cardinality budget check for the observability capstone (Chapter 19.7).

Reuses the estimator and linter from code/part20/c15_cardinality.py (Chapter
20.15). This script adds the platform rule: the families the platform declares,
plus the series reserved for Kubernetes components, must fit the Prometheus
series budget. It also lints a real /metrics exposition for forbidden labels.

Usage:
  python3 c07_cardinality_budget.py spec c07_metric_spec.json
  python3 c07_cardinality_budget.py scan metrics.txt
Exit code 1 when a check fails.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "part20"))
import c15_cardinality as c15  # noqa: E402


def check_spec(spec):
    """Return (ok, report dict). ok is False on a lint error or a blown budget."""
    est = c15.estimate(spec)
    reserved = int(spec.get("reserved_for_kubernetes", 0))
    findings = c15.lint_spec(spec)
    errors = [f for f in findings if f.level == "error"]
    used = est["total"] + reserved
    budget = est["total_budget"]
    over = used > budget
    return (not errors and not over), {
        "declared": est["total"],
        "reserved": reserved,
        "used": used,
        "budget": budget,
        "headroom": budget - used,
        "lint_errors": [str(f) for f in errors],
        "families": est["families"],
    }


def check_exposition(text):
    findings = c15.lint_exposition(text)
    errors = [str(f) for f in findings if f.level == "error"]
    return not errors, errors


def main(argv):
    if len(argv) != 3 or argv[1] not in ("spec", "scan"):
        print(__doc__)
        return 2
    if argv[1] == "spec":
        ok, rep = check_spec(json.loads(pathlib.Path(argv[2]).read_text()))
        for name, n in sorted(rep["families"], key=lambda r: -r[1]):
            print(f"{n:>10,}  {name}")
        print(f"declared {rep['declared']:,} + reserved {rep['reserved']:,} = {rep['used']:,}"
              f" of {rep['budget']:,} (headroom {rep['headroom']:,})")
        for e in rep["lint_errors"]:
            print("FAIL", e)
    else:
        ok, errs = check_exposition(pathlib.Path(argv[2]).read_text())
        for e in errs:
            print("FAIL", e)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
