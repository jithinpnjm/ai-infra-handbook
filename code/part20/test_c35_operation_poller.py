import random

import pytest

from c35_operation_poller import (
    ApiError, FakeClock, FakeOperationServer, Operation, OperationFailed,
    OperationTimeout, RETRY_CALL, RETRY_NOTHING, RETRY_UNIT_OF_WORK, error_backoff,
    is_retriable, wait_operation)


def running(i="op-1"):
    return Operation(id=i)


def done(i="op-1", code="OK", msg="", rid="res-a"):
    return Operation(id=i, status_code=code, status_message=msg, resource_id=rid)


def run(server, clock, op=None, **kw):
    kw.setdefault("error_backoff_fn", lambda n: min(30.0, 2.0 ** (n - 1)))
    return wait_operation(op or running(), server.get, clock, **kw)


def test_success_after_running_polls():
    s = FakeOperationServer(script={"op-1": [running(), running(), done()]})
    c = FakeClock()
    result = run(s, c)
    assert result.successful and result.resource_id == "res-a"
    assert len(s.gets) == 3
    assert c.sleeps == [1.0, 1.0, 1.0]


def test_already_done_makes_no_call():
    s = FakeOperationServer()
    c = FakeClock()
    assert run(s, c, op=done()).successful
    assert s.gets == [] and c.sleeps == []


def test_synchronous_failure_is_raised_without_polling():
    s = FakeOperationServer()
    with pytest.raises(OperationFailed):
        run(s, FakeClock(), op=done(code="FAILED_PRECONDITION", msg="x"))
    assert s.gets == []


def test_failed_operation_raises_with_status():
    s = FakeOperationServer(script={"op-1": [running(), done(code="RESOURCE_EXHAUSTED", msg="quota")]})
    with pytest.raises(OperationFailed) as ei:
        run(s, FakeClock())
    assert ei.value.op.status_code == "RESOURCE_EXHAUSTED"
    assert "quota" in str(ei.value)


def test_timeout_reports_operation_id_and_last_state():
    s = FakeOperationServer(script={"op-1": [running()]})
    c = FakeClock()
    with pytest.raises(OperationTimeout) as ei:
        run(s, c, timeout=5.0)
    assert ei.value.op_id == "op-1" and not ei.value.last_seen.done
    assert c.now == pytest.approx(5.0)          # slept up to the deadline, not past it
    assert len(s.gets) == 5


def test_retriable_poll_errors_back_off_then_recover():
    err = ApiError("UNAVAILABLE", "blip")
    s = FakeOperationServer(script={"op-1": [err, err, err, done()]})
    c = FakeClock()
    assert run(s, c).successful
    assert c.sleeps == [1.0, 1.0, 2.0, 4.0]     # interval, then 1,2,4 backoff for errors 1..3


def test_error_streak_resets_after_a_good_poll():
    err = ApiError("UNAVAILABLE", "blip")
    s = FakeOperationServer(script={"op-1": [err, running(), err, done()]})
    c = FakeClock()
    run(s, c)
    assert c.sleeps == [1.0, 1.0, 1.0, 1.0]     # second error restarts at attempt 1


def test_non_retriable_poll_error_is_raised_at_once():
    s = FakeOperationServer(script={"op-1": [ApiError("PERMISSION_DENIED", "no")]})
    with pytest.raises(ApiError) as ei:
        run(s, FakeClock())
    assert ei.value.code == "PERMISSION_DENIED" and len(s.gets) == 1


def test_error_budget_can_cap_poll_errors():
    s = FakeOperationServer(script={"op-1": [ApiError("UNAVAILABLE", "down")]})
    with pytest.raises(ApiError):
        run(s, FakeClock(), max_poll_errors=3, timeout=1000)
    assert len(s.gets) == 4


def test_retry_type_overrides_code():
    assert is_retriable(ApiError("INTERNAL", "x", retry_type=RETRY_CALL))
    assert not is_retriable(ApiError("UNAVAILABLE", "x", retry_type=RETRY_NOTHING))
    assert not is_retriable(ApiError("UNAVAILABLE", "x", retry_type=RETRY_UNIT_OF_WORK))
    assert is_retriable(ApiError("RESOURCE_EXHAUSTED", "rate"))
    assert not is_retriable(ApiError("DEADLINE_EXCEEDED", "x", retry_type=RETRY_CALL))
    assert not is_retriable(ValueError("x"))


def test_backoff_is_capped_and_jittered_within_bounds():
    rng = random.Random(7)
    for attempt in range(1, 12):
        d = error_backoff(attempt, rng=rng)
        raw = min(30.0, 2 ** (attempt - 1))
        assert 0 < d <= 30.0
        assert raw * 0.8 - 1e-9 <= d or d == 30.0


def test_idempotent_create_survives_a_lost_response():
    s = FakeOperationServer(script={"op-1": [done()]})
    key = "7f95c54a-ee0e-4f8c-a64c-c9e0aac605a0"
    with pytest.raises(ApiError):
        s.create(key, "a", lose_response=True)
    op = s.create(key, "a")                      # retry with the same key
    assert len(s.creates) == 1 and op.id == "op-1"
    assert run(s, FakeClock(), op=op).successful


def test_new_key_would_have_created_a_second_resource():
    s = FakeOperationServer()
    s.create("k1", "a")
    s.create("k2", "a")
    assert len(s.creates) == 2
