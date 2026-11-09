#!/usr/bin/env python3
"""Flag risky changes in `terraform show -json plan.bin` output.

Reads the plan JSON representation (format_version 1.x) and reports
destroys and replacements of stateful resources, any other destroy, and
node-group capacity shrinks. Standard library only.

Usage:
  terraform plan -out=plan.bin && terraform show -json plan.bin > plan.json
  python3 c24_plan_risk.py plan.json [--fail-on HIGH] [--allow ADDRESS ...]

Exit code: 0 clean, 1 a finding at or above --fail-on, 2 unreadable plan.
"""
import argparse
import json
import sys

LEVELS = {"INFO": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

# Types whose loss cannot be undone by re-running apply.
STATEFUL_TYPES = frozenset({
    "nebius_mk8s_v1_cluster",
    "nebius_mk8s_v1_node_group",
    "nebius_compute_v1_filesystem",
    "nebius_compute_v1_disk",
    "nebius_compute_v1_gpu_cluster",
    "nebius_storage_v1_bucket",
    "nebius_msp_postgresql_v1alpha1_cluster",
    "nebius_kms_v1_symmetric_key",
    "nebius_kms_v1_asymmetric_key",
    "nebius_mysterybox_v1_secret",
    "nebius_vpc_v1_network",
    "nebius_vpc_v1_subnet",
})


class PlanError(Exception):
    """The input is not a plan JSON this tool understands."""


def kind_of(actions):
    """Map the documented actions list to one word."""
    a = list(actions)
    if a == ["no-op"]:
        return "no-op"
    if a == ["create"]:
        return "create"
    if a == ["read"]:
        return "read"
    if a == ["update"]:
        return "update"
    if a == ["delete"]:
        return "delete"
    if a == ["delete", "create"]:
        return "replace"
    if a == ["create", "delete"]:
        return "replace-create-first"
    raise PlanError("unknown actions list: %r" % (a,))


def load_plan(text):
    try:
        plan = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PlanError("not JSON: %s" % exc)
    if not isinstance(plan, dict) or "format_version" not in plan:
        raise PlanError("no format_version: is this `terraform show -json` of a plan?")
    major = str(plan["format_version"]).split(".")[0]
    if major != "1":
        raise PlanError("unsupported format_version %s" % plan["format_version"])
    if "resource_changes" not in plan:
        raise PlanError("no resource_changes key")
    return plan


def _finding(level, rc, kind, message):
    return {
        "level": level,
        "address": rc["address"],
        "kind": kind,
        "reason": rc.get("action_reason"),
        "message": message,
    }


def analyse(plan, stateful_types=STATEFUL_TYPES, allow=()):
    """Return a list of findings, worst first."""
    findings = []
    if plan.get("errored"):
        findings.append({"level": "CRITICAL", "address": "(plan)", "kind": "errored",
                         "reason": None, "message": "plan is marked errored: do not apply"})
    for rc in plan["resource_changes"]:
        kind = kind_of(rc["change"]["actions"])
        if kind in ("no-op", "create", "read") or rc["address"] in allow:
            continue
        stateful = rc["type"] in stateful_types
        if kind in ("delete", "replace", "replace-create-first"):
            if stateful:
                what = "destroys" if kind == "delete" else "replaces"
                findings.append(_finding(
                    "CRITICAL", rc, kind,
                    "plan %s stateful %s" % (what, rc["type"])))
            else:
                findings.append(_finding(
                    "MEDIUM", rc, kind, "plan destroys or replaces %s" % rc["type"]))
        if kind == "update" and rc["type"] == "nebius_mk8s_v1_node_group":
            before = (rc["change"].get("before") or {}).get("fixed_node_count")
            after = (rc["change"].get("after") or {}).get("fixed_node_count")
            if isinstance(before, int) and isinstance(after, int) and after < before:
                findings.append(_finding(
                    "HIGH", rc, kind,
                    "node group shrinks from %d to %d nodes" % (before, after)))
    findings.sort(key=lambda f: -LEVELS[f["level"]])
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("plan", help="plan JSON file, or - for stdin")
    ap.add_argument("--fail-on", choices=["MEDIUM", "HIGH", "CRITICAL"], default="HIGH")
    ap.add_argument("--allow", action="append", default=[],
                    help="resource address whose destroy was approved in review")
    args = ap.parse_args(argv)
    try:
        text = sys.stdin.read() if args.plan == "-" else open(args.plan).read()
        findings = analyse(load_plan(text), allow=set(args.allow))
    except (PlanError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    for f in findings:
        why = " (%s)" % f["reason"] if f["reason"] else ""
        print("%-8s %s: %s%s" % (f["level"], f["address"], f["message"], why))
    if not findings:
        print("OK: no destroy, replace or shrink in this plan")
    worst = max((LEVELS[f["level"]] for f in findings), default=-1)
    return 1 if worst >= LEVELS[args.fail_on] else 0


if __name__ == "__main__":
    sys.exit(main())
