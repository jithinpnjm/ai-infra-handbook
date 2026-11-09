#!/usr/bin/env python3
"""Cardinality estimator and label-policy linter for Prometheus metric families.

Standard library only. Three commands:
  estimate SPEC.json   series count per family, total, and disk estimate
  lint SPEC.json       policy violations in a declared metric design
  scan METRICS.txt     policy violations in real /metrics exposition text
Exit code 1 when any error is found.
"""
import argparse
import json
import re
import sys
from collections import defaultdict

# Labels that identify one request, one person, or one prompt. Never allowed.
FORBIDDEN_LABELS = frozenset({
    "request_id", "req_id", "trace_id", "span_id", "user_id", "user",
    "email", "session_id", "prompt_hash", "prompt", "completion",
    "ip", "client_ip", "remote_addr", "url", "uuid", "timestamp",
    "api_key", "token",
})
# Names that are often fine when bounded, so they need a declared bound.
SUSPECT_SUFFIXES = ("_id", "_uuid", "_hash")

TYPES = {"counter", "gauge", "histogram", "summary"}
NAME_RE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
LABEL_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
BAD_UNIT_SUFFIXES = ("_ms", "_milliseconds", "_us", "_microseconds",
                     "_kb", "_mb", "_gb", "_kilobytes", "_megabytes")

DEFAULT_LIMITS = {
    "max_label_values": 1000,      # per label
    "family_budget": 200_000,      # series per family
    "total_budget": 2_000_000,     # series per Prometheus shard
    "max_buckets": 25,
    "max_labels": 10,
}


class Finding:
    def __init__(self, level, family, rule, message):
        self.level, self.family, self.rule, self.message = level, family, rule, message

    def __str__(self):
        return f"{self.level.upper():5} {self.family}: [{self.rule}] {self.message}"

    def as_tuple(self):
        return (self.level, self.family, self.rule)


def series_per_combo(mtype, buckets=0, quantiles=0):
    """Series one label combination produces.

    A histogram has one series per finite bucket, one for +Inf, plus _sum
    and _count. A summary has one per quantile plus _sum and _count.
    """
    if mtype == "histogram":
        return buckets + 1 + 2
    if mtype == "summary":
        return quantiles + 2
    return 1


def family_series(fam):
    """Upper-bound series count for one declared family.

    combos is the product of label value counts. `fill` is the assumed share
    of that product that really occurs, and `targets` is how many scrape
    targets expose the family.
    """
    combos = 1
    for count in fam.get("labels", {}).values():
        if isinstance(count, int) and count > 0:
            combos *= count
    fill = float(fam.get("fill", 1.0))
    targets = int(fam.get("targets", 1))
    per = series_per_combo(fam.get("type", "gauge"),
                           int(fam.get("buckets", 0)),
                           int(fam.get("quantiles", 0)))
    return int(combos * fill) * per * targets


def disk_bytes(series, scrape_interval_s, retention_s, bytes_per_sample=2.0):
    """Prometheus storage page formula:
    retention seconds * samples per second * bytes per sample."""
    samples_per_s = series / scrape_interval_s
    return retention_s * samples_per_s * bytes_per_sample


def estimate(spec):
    limits = {**DEFAULT_LIMITS, **spec.get("limits", {})}
    rows = []
    for fam in spec["families"]:
        rows.append((fam["name"], family_series(fam)))
    total = sum(n for _, n in rows)
    interval = float(spec.get("scrape_interval_s", 30))
    retention = float(spec.get("retention_s", 15 * 86400))
    return {
        "families": rows,
        "total": total,
        "total_budget": limits["total_budget"],
        "disk_bytes_low": disk_bytes(total, interval, retention, 1.0),
        "disk_bytes_high": disk_bytes(total, interval, retention, 2.0),
    }


def lint_spec(spec):
    limits = {**DEFAULT_LIMITS, **spec.get("limits", {})}
    findings = []
    for fam in spec["families"]:
        name = fam.get("name", "")
        mtype = fam.get("type", "")
        labels = fam.get("labels", {})

        def add(level, rule, msg):
            findings.append(Finding(level, name or "?", rule, msg))

        if not NAME_RE.match(name):
            add("error", "name-syntax", "metric name has invalid characters")
        if mtype not in TYPES:
            add("error", "type", f"type must be one of {sorted(TYPES)}")
        if mtype == "counter" and not name.endswith("_total"):
            add("error", "counter-suffix", "counter names must end in _total")
        if mtype == "gauge" and name.endswith("_total"):
            add("error", "gauge-suffix", "_total is reserved for counters")
        if name.endswith(BAD_UNIT_SUFFIXES):
            add("warn", "base-unit", "use base units: seconds and bytes")
        if len(labels) > limits["max_labels"]:
            add("error", "too-many-labels", f"{len(labels)} labels, limit {limits['max_labels']}")
        if mtype == "histogram" and int(fam.get("buckets", 0)) > limits["max_buckets"]:
            add("warn", "too-many-buckets", "each bucket multiplies series per label combination")
        if mtype == "histogram" and int(fam.get("buckets", 0)) == 0:
            add("error", "histogram-buckets", "histogram needs a bucket count")
        for label, count in labels.items():
            if not LABEL_RE.match(label) or label.startswith("__"):
                add("error", "label-syntax", f"label '{label}' is invalid or reserved")
                continue
            if label in FORBIDDEN_LABELS:
                add("error", "forbidden-label",
                    f"label '{label}' identifies a request or a person. Put it in a log or a trace.")
                continue
            if label == "le" and mtype != "histogram":
                add("error", "reserved-label", "le is reserved for histograms")
            if label == "quantile" and mtype != "summary":
                add("error", "reserved-label", "quantile is reserved for summaries")
            if not isinstance(count, int) or count <= 0:
                add("error", "unbounded-label", f"label '{label}' has no declared bound")
                continue
            if label.endswith(SUSPECT_SUFFIXES) and count > limits["max_label_values"] // 10:
                add("warn", "suspect-label", f"'{label}' looks like an identifier with {count} values")
            if count > limits["max_label_values"]:
                add("error", "label-values",
                    f"label '{label}' has {count} values, limit {limits['max_label_values']}")
        series = family_series(fam)
        if series > limits["family_budget"]:
            add("error", "family-budget",
                f"{series} series exceeds family budget {limits['family_budget']}")
    total = sum(family_series(f) for f in spec["families"])
    if total > limits["total_budget"]:
        findings.append(Finding("error", "*", "total-budget",
                                f"{total} series exceeds total budget {limits['total_budget']}"))
    return findings


_SAMPLE_RE = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(.*)\})?\s+\S+")
_PAIR_RE = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)="((?:[^"\\]|\\.)*)"')
_TYPE_RE = re.compile(r"^#\s*TYPE\s+(\S+)\s+(\S+)")


def parse_exposition(text):
    """Return {family: {"type": str, "series": set, "labels": {name: set(values)}}}.

    Histogram and summary children (_bucket, _sum, _count) fold into the
    family named in the TYPE line. The le and quantile labels are ignored.
    """
    types = {}
    fams = defaultdict(lambda: {"type": "untyped", "series": set(), "labels": defaultdict(set)})
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _TYPE_RE.match(line)
        if m:
            types[m.group(1)] = m.group(2)
            continue
        if line.startswith("#"):
            continue
        m = _SAMPLE_RE.match(line)
        if not m:
            continue
        name, body = m.group(1), m.group(2) or ""
        base = name
        for suffix in ("_bucket", "_sum", "_count"):
            if name.endswith(suffix) and name[: -len(suffix)] in types:
                base = name[: -len(suffix)]
                break
        pairs = _PAIR_RE.findall(body)
        fam = fams[base]
        fam["type"] = types.get(base, fam["type"])
        fam["series"].add((name, tuple(sorted(pairs))))
        for key, value in pairs:
            if key in ("le", "quantile"):
                continue
            fam["labels"][key].add(value)
    return fams


def lint_exposition(text, max_label_values=None):
    limit = max_label_values or DEFAULT_LIMITS["max_label_values"]
    findings = []
    for name, fam in sorted(parse_exposition(text).items()):
        for label, values in fam["labels"].items():
            if label in FORBIDDEN_LABELS:
                findings.append(Finding("error", name, "forbidden-label",
                                        f"label '{label}' present with {len(values)} values"))
            elif len(values) > limit:
                findings.append(Finding("error", name, "label-values",
                                        f"label '{label}' has {len(values)} values, limit {limit}"))
        if fam["type"] == "counter" and not name.endswith("_total"):
            findings.append(Finding("warn", name, "counter-suffix", "counter without _total"))
    return findings


def _fmt_bytes(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1000:
            return f"{n:.1f} {unit}"
        n /= 1000
    return f"{n:.1f} PB"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["estimate", "lint", "scan"])
    ap.add_argument("path")
    args = ap.parse_args(argv)
    if args.command == "scan":
        with open(args.path) as fh:
            findings = lint_exposition(fh.read())
    else:
        with open(args.path) as fh:
            spec = json.load(fh)
        if args.command == "estimate":
            result = estimate(spec)
            for name, n in sorted(result["families"], key=lambda r: -r[1]):
                print(f"{n:>12,}  {name}")
            print(f"{result['total']:>12,}  TOTAL (budget {result['total_budget']:,})")
            print(f"disk for the retention window: {_fmt_bytes(result['disk_bytes_low'])}"
                  f" to {_fmt_bytes(result['disk_bytes_high'])} at 1 to 2 bytes per sample")
            return 0
        findings = lint_spec(spec)
    for f in findings:
        print(f)
    errors = [f for f in findings if f.level == "error"]
    print(f"{len(errors)} errors, {len(findings) - len(errors)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
