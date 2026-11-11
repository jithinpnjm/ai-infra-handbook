"""Chapter 11.32: version-skew and recycle arithmetic."""
import pytest

import c32_upgrade_planner as up


def test_one_minor_up_is_allowed_and_two_is_not():
    up.check_cp_step("1.36.3", "1.37.2")
    with pytest.raises(up.SkewError):
        up.check_cp_step("1.35.3", "1.37.2")


def test_patch_bump_allowed_downgrade_and_same_refused():
    up.check_cp_step("1.36.3", "1.36.4")
    for bad in ("1.36.2", "1.36.3", "1.35.9"):
        with pytest.raises(up.SkewError):
            up.check_cp_step("1.36.3", bad)


def test_leading_v_refused():
    with pytest.raises(up.SkewError):
        up.parse("v1.36.3")


def test_worker_skew_n_minus_3():
    up.check_worker_skew({"a": "1.34.2"}, "1.37.2")
    with pytest.raises(up.SkewError):
        up.check_worker_skew({"a": "1.33.9"}, "1.37.2")


def test_path_is_one_minor_per_hop_using_available_images():
    assert up.cp_path("1.34.2", "1.37.2", ["1.35.3", "1.35.1", "1.36.3"]) == ["1.35.3", "1.36.3", "1.37.2"]
    assert up.cp_path("1.36.3", "1.36.5") == ["1.36.5"]


def test_plan_orders_control_plane_before_pools_oldest_pool_first():
    acts = up.plan("1.36.3", "1.37.2", {"gpu": "1.36.3", "cpu": "1.35.3"})
    assert acts == [("patch-cluster", "1.37.2"), ("patch-nodepool", "cpu", "1.37.2"), ("patch-nodepool", "gpu", "1.37.2")]


def test_plan_refuses_when_a_pool_would_fall_out_of_skew():
    with pytest.raises(up.SkewError):
        up.plan("1.33.0", "1.37.2", {"gpu": "1.33.0"})


def test_documented_recycle_example():
    # desiredNodeCount 4, recycleBudget 2, one node NotReady: at most one mark.
    assert up.recycle_marks(desired=4, available=3, budget=2) == 1


def test_recycle_marks_never_negative_and_zero_budget_marks_nothing():
    assert up.recycle_marks(4, 1, 2) == 0
    assert up.recycle_marks(4, 4, 0) == 0
    assert up.recycle_marks(4, 4, 2) == 2


def test_recycle_rounds():
    assert up.recycle_rounds(8, 8, 2) == 4
    assert up.recycle_rounds(8, 0, 0) == 0
    with pytest.raises(up.SkewError):
        up.recycle_rounds(8, 3, 0)


def test_control_plane_quorum_arithmetic():
    cp3 = up.ControlPlane(3)
    assert (cp3.quorum(), cp3.survivable_failures()) == (2, 1)
    assert cp3.replace_one_at_a_time_is_safe()
    assert not up.ControlPlane(1).replace_one_at_a_time_is_safe()
    assert up.ControlPlane(1, max_surge=1).replace_one_at_a_time_is_safe()
    assert up.ControlPlane(5).survivable_failures() == 2
