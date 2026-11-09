import math
import pytest
import slo_burn_rate as b


@pytest.mark.parametrize("slo,minutes", [
    (0.99, 432.0), (0.999, 43.2), (0.9995, 21.6), (0.9999, 4.32)])
def test_budget_minutes_30_days(slo, minutes):
    assert b.budget_minutes(slo) == pytest.approx(minutes)


def test_budget_minutes_28_days():
    assert b.budget_minutes(0.999, 28) == pytest.approx(40.32)


def test_burn_rate_and_threshold_roundtrip():
    assert b.burn_rate(0.0144, 0.999) == pytest.approx(14.4)
    assert b.error_ratio_threshold(14.4, 0.999) == pytest.approx(0.0144)


@pytest.mark.parametrize("burn,window,expected", [
    (14.4, 1, 0.02), (6, 6, 0.05), (1, 72, 0.10)])
def test_workbook_budget_consumed(burn, window, expected):
    assert b.budget_consumed(burn, window) == pytest.approx(expected)


def test_hours_to_exhaustion():
    assert b.hours_to_exhaustion(1) == 720
    assert b.hours_to_exhaustion(14.4) == pytest.approx(50)
    assert math.isinf(b.hours_to_exhaustion(0))


def test_total_outage_detection_seconds():
    m = b.minutes_to_detect(1.0, 0.999, 14.4, 1.0)
    assert m * 60 == pytest.approx(51.84)


def test_detection_none_when_below_threshold():
    assert b.minutes_to_detect(0.01, 0.999, 14.4, 1.0) is None


def test_multiwindow_needs_both_windows():
    assert b.should_alert(0.02, 0.02, 0.999, 14.4)
    assert not b.should_alert(0.02, 0.0, 0.999, 14.4)  # blip already over
    assert not b.should_alert(0.0, 0.5, 0.999, 14.4)  # spike too short


def test_invalid_slo():
    with pytest.raises(ValueError):
        b.error_budget(1.0)


def test_alert_table_matches_workbook():
    rows = b.alert_table(0.999)
    assert [r["burn"] for r in rows] == [14.4, 6.0, 1.0]
    assert [r["severity"] for r in rows] == ["page", "page", "ticket"]
    assert rows[1]["threshold"] == pytest.approx(0.006)
