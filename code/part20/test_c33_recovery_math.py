import pytest
from c33_recovery_math import (downtime_minutes, serial_availability,
    parallel_availability, lost_work_minutes, lost_gpu_hours,
    transfer_seconds, quorum, tolerated_failures)


def test_downtime_999_month():
    assert downtime_minutes(0.999) == pytest.approx(43.2)


def test_downtime_9999_month():
    assert downtime_minutes(0.9999) == pytest.approx(4.32)


def test_serial_is_worse_than_either_part():
    assert serial_availability(0.999, 0.999) == pytest.approx(0.998001)
    assert downtime_minutes(0.998001) == pytest.approx(86.4, abs=0.1)


def test_parallel_independent():
    assert parallel_availability(0.999, 0.999) == pytest.approx(0.999999)


def test_lost_work():
    assert lost_work_minutes(30) == (30, 15.0)
    assert lost_gpu_hours(512, 30) == 256.0
    assert lost_gpu_hours(512, 15) == 128.0


def test_transfer():
    assert transfer_seconds(1120, 5) == pytest.approx(224.0)


@pytest.mark.parametrize("n,q,t", [(1, 1, 0), (2, 2, 0), (3, 2, 1), (4, 3, 1), (5, 3, 2)])
def test_quorum(n, q, t):
    assert quorum(n) == q
    assert tolerated_failures(n) == t
