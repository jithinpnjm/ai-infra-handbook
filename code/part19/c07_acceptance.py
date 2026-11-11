#!/usr/bin/env python3
"""Acceptance runner for the observability capstone (Chapter 19.7).

Runs every offline check and prints one PASS or FAIL line each. With --e2e it
also runs the Docker end-to-end test (c07_e2e.py). Needs promtool and amtool on
PATH. Exit code 1 if anything fails.

Offline checks:
  rules        promtool check rules and promtool test rules (platform rules)
  slo          synthetic fault scenarios: promtool result equals the Python model
  alertmanager amtool check-config, and amtool route tests for the real file
  dashboard    structure, datasources, variables, every PromQL expression parses
  cardinality  declared series fit the budget; the bad spec is rejected
"""
import pathlib
import subprocess
import sys

import c07_cardinality_budget
import c07_dashboard_check
import c07_signals

HERE = pathlib.Path(__file__).resolve().parent
ROUTES = [   # (labels, expected receiver)
    (["alertname=Watchdog", "severity=none"], "deadman"),
    (["alertname=GatewayAvailabilityBurnFast", "severity=page"], "oncall-page"),
    (["alertname=GPUXidError", "severity=ticket", "area=gpu"], "ticket-queue"),
    (["alertname=SomethingUnlabelled"], "ticket-queue"),
]


def run(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    return r.returncode, (r.stdout + r.stderr).strip()


def checks():
    out = []
    rc, txt = run("promtool", "check", "rules", "c07_stack_rules.yaml", "c07_e2e_rules.yaml")
    out.append(("promtool check rules", rc == 0, txt))
    rc, txt = run("promtool", "test", "rules", "c07_rules_test.yaml")
    out.append(("promtool test rules (platform rules)", rc == 0, txt))
    for sc in c07_signals.SCENARIOS:
        ok, txt = c07_signals.run_promtool(sc)
        out.append((f"slo scenario: {sc.name}", ok, txt))
    rc, txt = run("amtool", "check-config", "c07_alertmanager.yaml")
    out.append(("amtool check-config", rc == 0, txt))
    for labels, want in ROUTES:
        rc, txt = run("amtool", "config", "routes", "test", "--config.file=c07_alertmanager.yaml", *labels)
        out.append((f"route {labels[0]} -> {want}", rc == 0 and txt.strip() == want, txt))
    errs, n = c07_dashboard_check.check_all(HERE / "c07_dashboard_gpu_platform.json")
    out.append((f"dashboard ({n} PromQL expressions)", not errs, "; ".join(errs)))
    import json
    ok, rep = c07_cardinality_budget.check_spec(json.loads((HERE / "c07_metric_spec.json").read_text()))
    out.append((f"cardinality: {rep['used']:,} of {rep['budget']:,} series", ok, str(rep["lint_errors"])))
    bad, _ = c07_cardinality_budget.check_spec(json.loads((HERE / "c07_metric_spec_bad.json").read_text()))
    out.append(("cardinality: spec with a user_id label is rejected", not bad, ""))
    return out


def main(argv):
    results = checks()
    if "--e2e" in argv:
        import c07_e2e
        results += [(r.name, r.ok, r.detail) for r in c07_e2e.run_e2e()]
    bad = 0
    for name, ok, detail in results:
        print(("PASS " if ok else "FAIL ") + name)
        if not ok:
            bad += 1
            print("     " + detail.replace("\n", "\n     "))
    print(f"{len(results) - bad} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
