#!/usr/bin/env python3
"""Regex-level PromQL pitfall linter. Standard library only.

It reads PromQL given with --expr or the rule expressions in Prometheus rule files,
and flags patterns that are valid PromQL but usually wrong. It does not parse
PromQL, so it can miss things and can misfire. Treat a finding as a question to ask.

Usage:
  c25_promql_lint.py --expr 'rate(x_total[30s])' [--scrape-interval 30s]
  c25_promql_lint.py [--strict] rules.yaml ...
Exit code 1 when an error is found (or any finding with --strict).
Add '# lint: ignore=P008' inside a rule block to silence a rule id there.
"""
import argparse
import re
import sys
from dataclasses import dataclass

UNITS = {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "y": 31536000}
AGG = r"(?:sum|avg|min|max|count|stddev|quantile|topk|bottomk)"
COUNTER_SUFFIXES = ("_total", "_count", "_sum", "_bucket")
GAUGE_WORDS = ("waiting", "running", "usage", "depth", "bytes", "perc", "ratio",
               "utilization", "temperature", "inflight")


@dataclass
class Finding:
    rule: str
    severity: str  # "error" or "warn"
    message: str
    expr: str
    line: int = 0

    def __str__(self):
        where = f"line {self.line}: " if self.line else ""
        return f"{self.severity.upper()} {self.rule} {where}{self.message}\n    {self.expr.strip()[:110]}"


def parse_duration(text):
    """'1h30m' -> 5400.0 seconds. Returns None when the text is not a duration."""
    parts = re.findall(r"(\d+)(ms|s|m|h|d|w|y)", text)
    if not parts or "".join(n + u for n, u in parts) != text:
        return None
    return float(sum(int(n) * UNITS[u] for n, u in parts))


def call_args(expr, name):
    """Yield (start, inner_text) for each call name( ... ) using balanced parentheses."""
    for m in re.finditer(r"\b" + name + r"\s*\(", expr):
        depth, i = 1, m.end()
        while i < len(expr) and depth:
            depth += {"(": 1, ")": -1}.get(expr[i], 0)
            i += 1
        yield m.start(), expr[m.end():i - 1]


def lint_expr(expr, scrape_s=30.0, kind="expr", line=0, has_labels_annotation=False):
    out = []

    def add(rule, sev, msg):
        out.append(Finding(rule, sev, msg, expr, line))

    # P001 range shorter than the scrape interval allows
    for fn in ("rate", "irate", "increase"):
        for _, inner in call_args(expr, fn):
            m = re.search(r"\[(\w+)\](?:\s*offset\s*\w+)?\s*$", inner.strip())
            sec = parse_duration(m.group(1)) if m else None
            if sec is None:
                continue
            if sec < 2 * scrape_s:
                add("P001", "error", f"{fn}() range {m.group(1)} holds fewer than 2 scrapes at a "
                    f"{scrape_s:g}s interval, so the result is empty or unstable")
            elif sec < 4 * scrape_s and fn != "irate":
                add("P001", "warn", f"{fn}() range {m.group(1)} is under 4 scrape intervals; "
                    "one missed scrape leaves a single sample")
    # P002 histogram_quantile must see le
    for _, inner in call_args(expr, "histogram_quantile"):
        arg = inner.split(",", 1)[1] if "," in inner else ""
        m = re.search(AGG + r"\s*(?:(by|without)\s*\(([^)]*)\)\s*)?\(", arg)
        if m:
            mode, labels = m.group(1), m.group(2) or ""
            if not mode:
                post = re.search(r"\)\s*(by|without)\s*\(([^)]*)\)\s*$", arg.strip())
                if post:
                    mode, labels = post.group(1), post.group(2)
            has_le = bool(re.search(r"\ble\b", labels))
            if not mode:
                add("P002", "error", "aggregation with no by() inside histogram_quantile drops the le label")
            elif mode == "by" and not has_le:
                add("P002", "error", "aggregation by() inside histogram_quantile does not keep le")
            elif mode == "without" and has_le:
                add("P002", "error", "aggregation without() removes le before histogram_quantile")
        elif re.search(r"\b(?:rate|irate|increase)\s*\(", arg):
            add("P002", "warn", "histogram_quantile over raw rate() gives one quantile per series; "
                "sum by (..., le) first if you want a fleet quantile")
    # P003 averaging quantiles
    for fn in ("avg", "avg_over_time"):
        for _, inner in call_args(expr, fn):
            if re.search(r"histogram_quantile|quantile\s*=\s*\"|\bp\d{2}\b|_p\d{2}\b", inner):
                add("P003", "error", f"{fn}() of a percentile is not a percentile of the combined data; "
                    "merge buckets, then take the quantile once")
    # P004 aggregate first, rate second
    for fn in ("rate", "irate", "increase"):
        for _, inner in call_args(expr, fn):
            if re.match(r"\s*" + AGG + r"\b", inner) and re.search(r"\[\w+:\w*\]\s*$", inner.strip()):
                add("P004", "error", f"{fn}() over an aggregate hides per-series counter resets; "
                    "take the rate first, then sum")
    # P005 irate in an alert
    if kind == "alert" and re.search(r"\birate\s*\(", expr):
        add("P005", "warn", "irate() uses the last two samples only, so alerts on it flap and miss bursts")
    # P006 rate over something that looks like a gauge
    for fn in ("rate", "irate", "increase"):
        for _, inner in call_args(expr, fn):
            m = re.match(r"\s*([A-Za-z_:][A-Za-z0-9_:]*)", inner)
            name = m.group(1) if m else ""
            if name and not name.endswith(COUNTER_SUFFIXES) and any(w in name for w in GAUGE_WORDS):
                add("P006", "warn", f"{fn}() on {name}, which looks like a gauge; "
                    "use avg_over_time, max_over_time or deriv")
    # P007 averaging a ratio
    for _, inner in call_args(expr, "avg"):
        if "ratio" in inner or "/" in inner:
            add("P007", "warn", "avg() of a ratio weights a quiet pod like a busy one; "
                "sum numerator and denominator separately, then divide")
    # P010 labels used in annotations but dropped by the aggregation
    if kind == "alert" and has_labels_annotation:
        top = re.search(r"\b" + AGG + r"\s*(by|without)?\s*\(?", expr)
        if top and not top.group(1) and re.match(r"\s*" + AGG + r"\s*\(", expr):
            add("P010", "warn", "aggregation without by() leaves no labels, but the annotation uses $labels")
    return out


def extract_rules(text):
    """Yield dicts: kind, name, expr, expr_line, has_for, annotations, ignore."""
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if re.match(r"\s*-\s*(alert|record):\s*\S+", l)]
    for n, s in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        for j in range(s + 1, end):
            if re.match(r"\s*-\s*name:", lines[j]):
                end = j
                break
        block = lines[s:end]
        head = re.match(r"\s*-\s*(alert|record):\s*(\S+)", block[0])
        rule = {"kind": "alert" if head.group(1) == "alert" else "record", "name": head.group(2),
                "expr": "", "expr_line": 0, "has_for": False, "annotations": "", "ignore": set()}
        for k, l in enumerate(block):
            if re.match(r"\s*for:", l):
                rule["has_for"] = True
            ig = re.search(r"#\s*lint:\s*ignore=([\w,]+)", l)
            if ig:
                rule["ignore"] |= set(ig.group(1).split(","))
            m = re.match(r"(\s*)expr:\s*(.*)$", l)
            if m:
                rule["expr_line"] = s + k + 1
                if m.group(2).strip() in ("|", ">", "|-", ">-"):
                    indent = len(m.group(1))
                    body = []
                    for l2 in block[k + 1:]:
                        if l2.strip() and len(l2) - len(l2.lstrip()) <= indent:
                            break
                        body.append(l2.strip())
                    rule["expr"] = " ".join(body)
                else:
                    rule["expr"] = m.group(2).strip()
            if "$labels" in l:
                rule["annotations"] += l
        yield rule


def lint_text(text, scrape_s=30.0):
    out = []
    for r in extract_rules(text):
        found = lint_expr(r["expr"], scrape_s, r["kind"], r["expr_line"], "$labels" in r["annotations"])
        if r["kind"] == "alert" and not r["has_for"]:
            found.append(Finding("P008", "warn", f"alert {r['name']} has no for: clause, so one bad "
                                 "evaluation pages", r["expr"], r["expr_line"]))
        if r["kind"] == "record" and r["name"].count(":") < 2:
            found.append(Finding("P009", "warn", f"record name {r['name']} is not level:metric:operations",
                                 r["expr"], r["expr_line"]))
        out.extend(f for f in found if f.rule not in r["ignore"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--expr", action="append", default=[])
    ap.add_argument("--scrape-interval", default="30s")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args(argv)
    scrape = parse_duration(a.scrape_interval)
    if scrape is None:
        ap.error("bad --scrape-interval")
    findings = []
    for e in a.expr:
        findings += lint_expr(e, scrape)
    for path in a.files:
        with open(path) as fh:
            for f in lint_text(fh.read(), scrape):
                f.expr = f"{path}: {f.expr}"
                findings.append(f)
    for f in findings:
        print(f)
    bad = [f for f in findings if f.severity == "error" or a.strict]
    print(f"{len(findings)} finding(s), {len(bad)} failing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
