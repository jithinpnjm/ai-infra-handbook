import copy
import json
import pathlib

import pytest

import c37_status_history as sh

FIX = pathlib.Path(__file__).with_name("c37_status_incidents_fixture.json")
AS_OF = sh.parse_ts("2026-11-11T00:00:00Z")


def mk(i, created, resolved, impact="major", comp="EU-NORTH1 - Compute Cloud"):
    return {"id": i, "name": i, "impact": impact, "created_at": created,
            "resolved_at": resolved,
            "incident_updates": [{"status": "investigating", "created_at": created,
                                  "affected_components": [{"name": comp}]}]}


def test_fixture_loads_and_counts():
    incs = sh.load_incidents(json.loads(FIX.read_text()))
    assert len(incs) == 50
    assert sum(i.has_postmortem for i in incs) == 1


def test_fixture_us_central1_postmortem_incident_duration():
    incs = {i.id: i for i in sh.load_incidents(json.loads(FIX.read_text()))}
    big = [i for i in incs.values() if i.name == "Region us-central1 partial degradation"][0]
    minutes = (big.end - big.start).total_seconds() / 60
    assert round(minutes) == 1293  # 2026-08-19 10:43 to 2026-08-20 08:16


def test_overlap_counts_once():
    data = {"incidents": [
        mk("a", "2026-11-01T00:00:00Z", "2026-11-01T02:00:00Z"),
        mk("b", "2026-11-01T01:00:00Z", "2026-11-01T03:00:00Z")]}
    rep = sh.component_report(sh.load_incidents(data), AS_OF)
    row = rep["rows"][0]
    assert row["incidents"] == 2 and row["down_minutes"] == 180.0


def test_availability_arithmetic():
    data = {"incidents": [mk("a", "2026-11-01T00:00:00Z", "2026-11-01T01:00:00Z")]}
    rep = sh.component_report(sh.load_incidents(data), AS_OF)
    # window is 10 days = 14400 min, down 60 min
    assert rep["window_minutes"] == 14400
    assert rep["rows"][0]["availability"] == pytest.approx(100 * (1 - 60 / 14400), abs=1e-3)


def test_min_impact_filters_minor():
    data = {"incidents": [mk("a", "2026-11-01T00:00:00Z", "2026-11-01T01:00:00Z", "minor")]}
    assert sh.component_report(sh.load_incidents(data), AS_OF)["rows"] == []
    assert len(sh.component_report(sh.load_incidents(data), AS_OF, "minor")["rows"]) == 1


def test_open_incident_runs_to_as_of():
    data = {"incidents": [mk("a", "2026-11-10T00:00:00Z", None)]}
    row = sh.component_report(sh.load_incidents(data), AS_OF)["rows"][0]
    assert row["down_minutes"] == 1440.0


def test_failure_resolved_before_created():
    data = {"incidents": [mk("a", "2026-11-01T02:00:00Z", "2026-11-01T01:00:00Z")]}
    with pytest.raises(sh.StatusDataError):
        sh.load_incidents(data)


def test_failure_bad_shapes():
    with pytest.raises(sh.StatusDataError):
        sh.load_incidents({"nope": []})
    bad = copy.deepcopy({"incidents": [mk("a", "yesterday", None)]})
    with pytest.raises(sh.StatusDataError):
        sh.load_incidents(bad)
    with pytest.raises(sh.StatusDataError):
        sh.component_report([], AS_OF)
    odd = {"incidents": [mk("a", "2026-11-01T00:00:00Z", None, impact="huge")]}
    with pytest.raises(sh.StatusDataError):
        sh.load_incidents(odd)


def test_region_grouping_and_ack_lag():
    data = {"incidents": [mk("a", "2026-11-01T00:00:00Z", "2026-11-01T01:00:00Z")]}
    incs = sh.load_incidents(data)
    rep = sh.component_report(incs, AS_OF, by="region")
    assert rep["rows"][0]["component"] == ("EU-NORTH1", "Compute Cloud")
    assert sh.public_ack_lag_minutes(incs[0]) == 0


def test_unattributed_incident_is_kept_visible():
    data = {"incidents": [{"id": "x", "name": "x", "impact": "major",
                           "created_at": "2026-11-01T00:00:00Z",
                           "resolved_at": "2026-11-01T01:00:00Z"}]}
    row = sh.component_report(sh.load_incidents(data), AS_OF)["rows"][0]
    assert row["component"] == "unattributed"
