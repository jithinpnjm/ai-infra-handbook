#!/usr/bin/env python3
"""Sanity-check a Prometheus rules file without Prometheus: structure, duplicate alert names, required
annotations/labels, balanced brackets, and (optionally) that DCGM_FI_* metrics exist in dcgm-exporter's CSV.
Usage: check_alert_rules.py rules.yml [--dcgm-csv default-counters.csv]  (promtool check rules is the real check)"""
import re
import sys

import yaml


def balanced(expr):
    stack = {"(": ")", "[": "]", "{": "}"}
    st = []
    for ch in expr:
        if ch in stack:
            st.append(stack[ch])
        elif ch in stack.values():
            if not st or st.pop() != ch:
                return False
    return not st


def main(path, dcgm_csv=None):
    doc = yaml.safe_load(open(path))
    known = None
    if dcgm_csv:
        known = {l.split(",")[0].strip() for l in open(dcgm_csv) if l.strip() and not l.startswith("#")}
    problems, names, n = [], set(), 0
    for g in doc["groups"]:
        for r in g["rules"]:
            n += 1
            nm = r.get("alert") or r.get("record")
            if nm in names:
                problems.append(f"duplicate rule name {nm}")
            names.add(nm)
            if not balanced(r["expr"]):
                problems.append(f"{nm}: unbalanced brackets in expr")
            if "alert" in r:
                if r.get("labels", {}).get("severity") not in ("page", "warn", "ticket"):
                    problems.append(f"{nm}: severity must be page|warn|ticket")
                for k in ("summary", "runbook"):
                    if k not in r.get("annotations", {}):
                        problems.append(f"{nm}: missing annotation {k}")
                if r.get("labels", {}).get("severity") == "page" and "for" not in r:
                    problems.append(f"{nm}: paging alert without 'for' (flapping risk)") if "Row" not in nm else None
            if known is not None:
                for m in re.findall(r"DCGM_FI_[A-Z0-9_]+", r["expr"]):
                    if m not in known:
                        problems.append(f"{nm}: {m} is not in the dcgm-exporter counters file")
    print(f"{n} rules in {len(doc['groups'])} groups")
    for p in problems:
        print("PROBLEM", p)
    return 1 if problems else 0


if __name__ == "__main__":
    csv = sys.argv[sys.argv.index("--dcgm-csv") + 1] if "--dcgm-csv" in sys.argv else None
    sys.exit(main(sys.argv[1], csv))
