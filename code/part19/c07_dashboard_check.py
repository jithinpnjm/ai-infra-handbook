#!/usr/bin/env python3
"""Dashboard-as-code check for the observability capstone (Chapter 19.7).

Standard library, plus promtool on PATH. For one Grafana dashboard JSON file:

  structure  uid, title, schemaVersion, unique panel ids, panels inside the
             24 column grid, no two panels overlapping
  datasource every panel and target uses a datasource uid from the allowed set
  variables  every $name used in an expression is a declared variable or a
             known Grafana macro
  promql     every Prometheus expression parses. Grafana macros and variables
             are replaced with plain values, the expressions are written as
             recording rules in a temporary file, and `promtool check rules`
             reads them. promtool is the parser Prometheus itself uses.

Usage: python3 c07_dashboard_check.py DASHBOARD.json
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ALLOWED_DS = {"prometheus": "prometheus", "loki": "loki"}   # uid -> type
MACROS = {"__rate_interval": "5m", "__interval": "1m", "__range": "6h"}
VAR_RE = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")


def load(path):
    return json.loads(pathlib.Path(path).read_text())


def panels_of(dash):
    for p in dash.get("panels", []):
        yield p
        for child in p.get("panels", []):
            yield child


def check_structure(dash):
    errs = []
    for key in ("uid", "title", "schemaVersion", "panels"):
        if key not in dash:
            errs.append(f"missing top-level key {key}")
    ids = [p.get("id") for p in panels_of(dash)]
    if len(ids) != len(set(ids)):
        errs.append("duplicate panel ids")
    if any(i is None for i in ids):
        errs.append("panel without id")
    boxes = []
    for p in panels_of(dash):
        g = p.get("gridPos")
        if not g:
            errs.append(f"panel {p.get('id')} has no gridPos")
            continue
        if g["x"] < 0 or g["x"] + g["w"] > 24:
            errs.append(f"panel {p['id']} leaves the 24 column grid")
        for q in boxes:
            if (g["x"] < q["x"] + q["w"] and q["x"] < g["x"] + g["w"]
                    and g["y"] < q["y"] + q["h"] and q["y"] < g["y"] + g["h"]):
                errs.append(f"panel {p['id']} overlaps another panel")
        boxes.append(g)
    return errs


def datasource_uid(ds):
    return ds.get("uid") if isinstance(ds, dict) else ds


def check_datasources(dash):
    errs = []
    for p in panels_of(dash):
        if p.get("type") == "row":
            continue
        uid = datasource_uid(p.get("datasource", {}))
        if uid not in ALLOWED_DS:
            errs.append(f"panel {p.get('id')} datasource {uid!r} not in {sorted(ALLOWED_DS)}")
        for t in p.get("targets", []):
            tuid = datasource_uid(t.get("datasource", p.get("datasource", {})))
            if tuid != uid:
                errs.append(f"panel {p.get('id')} target datasource {tuid!r} differs from panel")
            if not t.get("refId"):
                errs.append(f"panel {p.get('id')} target without refId")
    return errs


def prom_expressions(dash):
    """Yield (label, expr) for every Prometheus query in the dashboard."""
    for p in panels_of(dash):
        if datasource_uid(p.get("datasource", {})) != "prometheus":
            continue
        for t in p.get("targets", []):
            if t.get("expr"):
                yield f"panel {p['id']} {t['refId']}", t["expr"]
    for v in dash.get("templating", {}).get("list", []):
        q = v.get("query")
        q = q.get("query") if isinstance(q, dict) else q
        if v.get("type") == "query" and datasource_uid(v.get("datasource", {})) == "prometheus" and q:
            m = re.fullmatch(r"\s*label_values\(\s*(.+?)\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*\)\s*", q)
            if m:   # label_values(selector, label): the selector must parse
                yield f"variable {v['name']}", m.group(1)
            else:
                yield f"variable {v['name']}", q


def check_variables(dash):
    declared = {v["name"] for v in dash.get("templating", {}).get("list", [])}
    errs = []
    for label, expr in prom_expressions(dash):
        for name in VAR_RE.findall(expr):
            if name not in declared and name not in MACROS:
                errs.append(f"{label} uses undeclared variable ${name}")
    return errs


def substitute(expr, variables):
    """Replace Grafana macros and variables by plain values a parser accepts.
    Variables become .+ (the allValue); macros become durations."""
    def repl(m):
        name = m.group(1)
        if name in MACROS:
            return MACROS[name]
        if name in variables:
            return ".+"
        return m.group(0)
    return VAR_RE.sub(repl, expr)


def check_promql(dash, promtool="promtool"):
    variables = {v["name"] for v in dash.get("templating", {}).get("list", [])}
    exprs = [(label, substitute(e, variables)) for label, e in prom_expressions(dash)]
    errs = []
    with tempfile.TemporaryDirectory() as d:
        # One file per expression so an error names the panel that caused it.
        for i, (label, expr) in enumerate(exprs):
            f = pathlib.Path(d) / f"e{i}.yaml"
            f.write_text("groups:\n  - name: dash\n    rules:\n"
                         f"      - record: c07:dashboard:expr{i}\n"
                         f"        expr: {json.dumps(expr)}\n")
            r = subprocess.run([promtool, "check", "rules", str(f)], capture_output=True, text=True)
            if r.returncode != 0:
                errs.append(f"{label}: {expr!r} does not parse: "
                            + (r.stdout + r.stderr).strip().splitlines()[-1])
    return errs, len(exprs)


def check_all(path, promtool="promtool"):
    dash = load(path)
    errs = check_structure(dash) + check_datasources(dash) + check_variables(dash)
    perrs, n = check_promql(dash, promtool)
    return errs + perrs, n


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    errs, n = check_all(argv[1])
    for e in errs:
        print("FAIL", e)
    print(f"{n} PromQL expressions checked, {len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
