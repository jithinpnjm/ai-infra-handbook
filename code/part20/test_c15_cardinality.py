import json
import os

import pytest

import c15_cardinality as cc

HERE = os.path.dirname(__file__)


def load(name):
    with open(os.path.join(HERE, name)) as fh:
        return json.load(fh)


def rules(findings):
    return {(f.family, f.rule) for f in findings}


def test_series_per_combo():
    assert cc.series_per_combo("counter") == 1
    assert cc.series_per_combo("gauge") == 1
    # 22 finite buckets + +Inf + _sum + _count
    assert cc.series_per_combo("histogram", buckets=22) == 25
    assert cc.series_per_combo("summary", quantiles=3) == 5


def test_family_series_multiplies_labels_fill_and_targets():
    fam = {"type": "counter", "labels": {"a": 10, "b": 5}, "fill": 0.5, "targets": 4}
    assert cc.family_series(fam) == 25 * 4
    hist = {"type": "histogram", "buckets": 4, "labels": {"m": 2}, "targets": 3}
    assert cc.family_series(hist) == 2 * 7 * 3


def test_disk_formula_matches_prometheus_storage_page():
    # 1000 series every 10 s is 100 samples/s. 1 day, 2 bytes each.
    assert cc.disk_bytes(1000, 10, 86400, 2.0) == pytest.approx(86400 * 100 * 2)


def test_estimate_good_spec_is_under_budget():
    out = cc.estimate(load("c15_inference_metrics.json"))
    assert out["total"] == 49200
    assert out["total"] < out["total_budget"]
    assert out["disk_bytes_low"] < out["disk_bytes_high"]
    assert dict(out["families"])["gateway_request_duration_seconds"] == 20 * 5 * 17 * 12


def test_lint_good_spec_has_no_findings():
    assert cc.lint_spec(load("c15_inference_metrics.json")) == []


def test_lint_bad_spec_catches_each_rule():
    got = rules(cc.lint_spec(load("c15_bad_metrics.json")))
    assert ("gateway_requests_total", "forbidden-label") in got
    assert ("gateway_requests_total", "family-budget") in got
    assert ("gateway_latency_ms", "forbidden-label") in got
    assert ("gateway_latency_ms", "base-unit") in got
    assert ("gateway_latency_ms", "too-many-buckets") in got
    assert ("queue_depth_total", "gauge-suffix") in got
    assert ("queue_depth_total", "unbounded-label") in got
    assert ("jobs_done", "counter-suffix") in got
    assert ("jobs_done", "reserved-label") in got
    assert ("*", "total-budget") in got


def test_tenant_on_every_gateway_family_breaks_the_budget():
    spec = load("c15_inference_metrics.json")
    for fam in spec["families"]:
        if fam["name"].startswith("gateway_"):
            fam["labels"]["tenant"] = 1000
            fam["fill"] = 0.1
    spec["limits"] = {"total_budget": 200_000}
    assert ("*", "total-budget") in rules(cc.lint_spec(spec))


def test_identifier_suffix_needs_small_bound():
    spec = {"families": [{"name": "x_total", "type": "counter",
                          "labels": {"tenant_id": 500}}]}
    assert ("x_total", "suspect-label") in rules(cc.lint_spec(spec))
    spec["families"][0]["labels"]["tenant_id"] = 20
    assert cc.lint_spec(spec) == []


def test_invalid_label_syntax_and_reserved_prefix():
    spec = {"families": [{"name": "x_total", "type": "counter",
                          "labels": {"9bad": 2, "__name2": 2}}]}
    assert ("x_total", "label-syntax") in rules(cc.lint_spec(spec))


EXPOSITION = '''# TYPE http_requests_total counter
http_requests_total{route="/a",code="200"} 5
http_requests_total{route="/b",code="500"} 1
# TYPE lat_seconds histogram
lat_seconds_bucket{route="/a",le="0.1"} 3
lat_seconds_bucket{route="/a",le="+Inf"} 5
lat_seconds_sum{route="/a"} 1.5
lat_seconds_count{route="/a"} 5
# TYPE leaky_total counter
leaky_total{request_id="a1"} 1
leaky_total{request_id="a2"} 1
# TYPE wide_total counter
wide_total{path="/x1"} 1
wide_total{path="/x2"} 1
wide_total{path="/x3"} 1
'''


def test_parse_exposition_folds_histogram_children():
    fams = cc.parse_exposition(EXPOSITION)
    lat = fams["lat_seconds"]
    assert lat["type"] == "histogram"
    assert len(lat["series"]) == 4
    assert "le" not in lat["labels"]
    assert fams["http_requests_total"]["labels"]["route"] == {"/a", "/b"}


def test_lint_exposition_flags_forbidden_and_wide_labels():
    got = rules(cc.lint_exposition(EXPOSITION, max_label_values=2))
    assert ("leaky_total", "forbidden-label") in got
    assert ("wide_total", "label-values") in got
    assert ("http_requests_total", "label-values") not in got


def test_parse_handles_escaped_quotes_and_no_labels():
    text = '# TYPE a gauge\na 1\na{k="x\\"y"} 2\n'
    fams = cc.parse_exposition(text)
    assert len(fams["a"]["series"]) == 2
    assert fams["a"]["labels"]["k"] == {'x\\"y'}


def test_cli_exit_codes(capsys):
    assert cc.main(["lint", os.path.join(HERE, "c15_inference_metrics.json")]) == 0
    assert cc.main(["lint", os.path.join(HERE, "c15_bad_metrics.json")]) == 1
    assert cc.main(["estimate", os.path.join(HERE, "c15_inference_metrics.json")]) == 0
    out = capsys.readouterr().out
    assert "TOTAL" in out and "49,200" in out
