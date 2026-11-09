import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c25_promql_lint as L  # noqa: E402

EX = json.load(open(os.path.join(HERE, "c25_exercises.json")))


def ids(findings):
    return {f.rule for f in findings}


def test_parse_duration():
    assert L.parse_duration("30s") == 30
    assert L.parse_duration("1h30m") == 5400
    assert L.parse_duration("5x") is None


@pytest.mark.parametrize("expr,sev", [
    ("rate(a_total[30s])", "error"),
    ("rate(a_total[1m])", "warn"),
    ("irate(a_total[1m])", None),
    ("rate(a_total[2m])", None),
    ("increase(a_total[45s])", "error"),
])
def test_range_window(expr, sev):
    found = [f for f in L.lint_expr(expr, 30) if f.rule == "P001"]
    assert (found[0].severity if found else None) == sev


def test_scrape_interval_changes_verdict():
    assert not [f for f in L.lint_expr("rate(a_total[1m])", 10) if f.rule == "P001"]


@pytest.mark.parametrize("expr,flagged", [
    ("histogram_quantile(0.99, sum(rate(x_bucket[5m])))", True),
    ("histogram_quantile(0.99, sum by (pod) (rate(x_bucket[5m])))", True),
    ("histogram_quantile(0.99, sum without (le) (rate(x_bucket[5m])))", True),
    ("histogram_quantile(0.99, sum(rate(x_bucket[5m])) by (job))", True),
    ("histogram_quantile(0.99, sum by (job, le) (rate(x_bucket[5m])))", False),
    ("histogram_quantile(0.99, sum(rate(x_bucket[5m])) by (le))", False),
    ("histogram_quantile(0.99, sum without (pod) (rate(x_bucket[5m])))", False),
    ("histogram_quantile(0.99, model_le:x_bucket:rate5m)", False),
])
def test_histogram_quantile_needs_le(expr, flagged):
    errors = [f for f in L.lint_expr(expr) if f.rule == "P002" and f.severity == "error"]
    assert bool(errors) == flagged


def test_raw_rate_quantile_is_only_a_warning():
    found = [f for f in L.lint_expr("histogram_quantile(0.9, rate(x_bucket[5m]))") if f.rule == "P002"]
    assert [f.severity for f in found] == ["warn"]


def test_average_of_quantiles():
    assert "P003" in ids(L.lint_expr("avg(histogram_quantile(0.99, sum by (pod, le) (rate(x_bucket[5m]))))"))
    assert "P003" in ids(L.lint_expr('avg(x_seconds{quantile="0.99"})'))
    assert "P003" not in ids(L.lint_expr("avg(rate(x_total[5m]))"))


def test_rate_of_aggregate_subquery():
    assert "P004" in ids(L.lint_expr("rate(sum(x_total)[5m:1m])"))
    assert "P004" not in ids(L.lint_expr("sum(rate(x_total[5m]))"))


def test_irate_only_matters_in_alerts():
    assert "P005" in ids(L.lint_expr("irate(x_total[5m]) > 1", kind="alert"))
    assert "P005" not in ids(L.lint_expr("irate(x_total[5m])", kind="record"))


def test_rate_on_gauge():
    assert "P006" in ids(L.lint_expr("rate(vllm:num_requests_waiting[5m])"))
    assert "P006" not in ids(L.lint_expr("rate(vllm:request_success_total[5m])"))


def test_average_of_ratio():
    assert "P007" in ids(L.lint_expr("avg(a_total / b_total)"))
    assert "P007" in ids(L.lint_expr("avg(job:errors:ratio_rate5m)"))
    assert "P007" not in ids(L.lint_expr("avg(vllm:kv_cache_usage_perc)"))


RULES = """groups:
  - name: g
    rules:
      - record: bad_name
        expr: sum(rate(a_total[5m]))
      - record: job:a:rate5m
        expr: sum by (job) (rate(a_total[5m]))
      - alert: NoFor
        expr: |
          up == 0
        labels: {severity: page}
      - alert: Ignored
        expr: up == 0   # lint: ignore=P008
      - alert: LostLabels
        expr: sum(rate(a_total[5m])) > 1
        for: 5m
        annotations:
          summary: "{{ $labels.model }}"
"""


def test_rule_file_extraction_and_rules():
    found = L.lint_text(RULES)
    got = sorted((f.rule, f.line) for f in found)
    assert ("P009", 5) in got
    assert ("P008", 9) in got
    assert ("P010", 15) in got
    assert not [f for f in found if f.rule == "P008" and f.line == 13]
    assert not [f for f in found if f.line == 7]


def test_good_rules_file_is_clean():
    text = open(os.path.join(HERE, "c25_trap_rules.yaml")).read()
    assert L.lint_text(text) == []


def test_bad_rules_file_is_flagged():
    text = open(os.path.join(HERE, "c25_bad_rules.yaml")).read()
    assert {"P005", "P007", "P008", "P009", "P010"} <= ids(L.lint_text(text))


@pytest.mark.parametrize("ex", EX["exercises"], ids=lambda e: e["id"])
def test_exercise_bad_is_flagged_and_fix_is_clean(ex):
    scrape = L.parse_duration(EX["scrape_interval"])
    kind = ex.get("kind", "expr")
    if ex["lint"]:
        assert ex["lint"] in ids(L.lint_expr(ex["bad"], scrape, kind))
    assert ex["lint"] not in ids(L.lint_expr(ex["fix"], scrape, "record"))
    assert not [f for f in L.lint_expr(ex["fix"], scrape, "record") if f.severity == "error"]


def test_cli_exit_codes():
    cli = os.path.join(HERE, "c25_promql_lint.py")
    bad = subprocess.run([sys.executable, cli, "--expr", "rate(a_total[10s])"], capture_output=True, text=True)
    assert bad.returncode == 1 and "P001" in bad.stdout
    ok = subprocess.run([sys.executable, cli, os.path.join(HERE, "c25_trap_rules.yaml")], capture_output=True, text=True)
    assert ok.returncode == 0
    warn = subprocess.run([sys.executable, cli, "--strict", os.path.join(HERE, "c25_bad_rules.yaml")],
                          capture_output=True, text=True)
    assert warn.returncode == 1
