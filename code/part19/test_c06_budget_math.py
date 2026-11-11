"""Tests for c06_budget_math.py (chapter 19.6)."""
import pytest

import c06_budget_math as b


def test_99_percent_is_hours_not_minutes():
    assert b.downtime_budget_minutes(0.99) == pytest.approx(438.0)          # 7.3 hours
    assert b.downtime_budget_minutes(0.999) == pytest.approx(43.8)
    assert b.downtime_budget_minutes(0.995) == pytest.approx(219.0)


def test_gpu_health_target_depends_on_pool_size():
    assert b.gpus_allowed_failing(0.98, 100) == 2
    assert b.gpus_allowed_failing(0.98, 32) == 0       # one bad GPU is already 3.1 percent


def test_one_node_of_four_is_a_quarter_of_the_pool():
    assert b.pool_fraction_lost(1, 4) == 0.25
    assert b.pool_fraction_lost(0, 4) == 0


def test_loop_latency_arithmetic():
    assert b.worst_case_detection_seconds() == 120
    assert b.worst_case_cordon_seconds() == 121
    assert b.worst_case_cordon_seconds(unhealthy_for=0) == 1
