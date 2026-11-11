"""Wait for a long-running Operation: poll, back off on retriable errors, stop at a deadline.

Modelled on what the public Go SDK does (operations.Operation.Wait and
conn.IsRetriableNebiusError) and on the API's Operation message: an operation is
done when its status is set, and successful when status.code is OK. Everything
here is offline. A FakeOperationServer replays a script, a FakeClock replaces
time, so tests run instantly and deterministically. Standard library only.
"""
import random
from dataclasses import dataclass, field
from typing import Callable, Optional

# gRPC status code names used by the Operation-compatible subset in operation.proto
OK = "OK"

# ServiceError.RetryType from error.proto
RETRY_UNSPECIFIED, RETRY_CALL, RETRY_UNIT_OF_WORK, RETRY_NOTHING = (
    "UNSPECIFIED", "CALL", "UNIT_OF_WORK", "NOTHING")

DEFAULT_RETRIABLE_CODES = frozenset({"RESOURCE_EXHAUSTED", "UNAVAILABLE"})


class ApiError(Exception):
    """An RPC failure: a gRPC code, an optional ServiceError retry_type, a message."""

    def __init__(self, code, message="", retry_type=RETRY_UNSPECIFIED, service_code=""):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.retry_type = retry_type
        self.service_code = service_code


@dataclass
class Operation:
    id: str
    status_code: Optional[str] = None      # None means still running (status unset)
    status_message: str = ""
    retry_type: str = RETRY_UNSPECIFIED    # from status.details ServiceError, if any
    resource_id: str = ""

    @property
    def done(self):
        return self.status_code is not None

    @property
    def successful(self):
        return self.status_code == OK


class OperationFailed(Exception):
    """The operation finished with a non-OK status. The attempt is over."""

    def __init__(self, op):
        super().__init__(f"operation {op.id} failed: {op.status_code}: {op.status_message}")
        self.op = op


class OperationTimeout(Exception):
    """Our deadline passed. The operation may still be running or may finish later.

    Never answer this by creating the resource again: look at the operation first."""

    def __init__(self, op_id, last_seen):
        super().__init__(f"gave up waiting for operation {op_id}")
        self.op_id = op_id
        self.last_seen = last_seen


def is_retriable(err):
    """Same order of decisions as the Go SDK: an explicit retry_type wins, then the code."""
    if not isinstance(err, ApiError):
        return False
    if err.code in ("CANCELLED", "DEADLINE_EXCEEDED"):
        return False
    if err.retry_type == RETRY_CALL:
        return True
    if err.retry_type in (RETRY_NOTHING, RETRY_UNIT_OF_WORK):
        return False
    return err.code in DEFAULT_RETRIABLE_CODES


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def error_backoff(attempt, base=1.0, cap=30.0, jitter=0.2, rng=random):
    """Exponential backoff for consecutive poll errors, capped, with +/- jitter.
    attempt starts at 1. Defaults mirror the Go SDK (1 s base, 30 s cap, 20% jitter)."""
    raw = min(cap, base * 2 ** (attempt - 1))
    return min(cap, raw * (1 + rng.uniform(-jitter, jitter)))


def wait_operation(op, get_operation, clock, *, interval=1.0, timeout=600.0,
                   error_backoff_fn: Callable = error_backoff, max_poll_errors=None):
    """Poll until op is done. Return the finished Operation or raise.

    get_operation(op_id) returns an Operation or raises ApiError.
    Raises OperationFailed on a non-OK status, OperationTimeout at the deadline,
    and the original ApiError for a non-retriable poll error."""
    deadline = clock.monotonic() + timeout
    if op.done:
        if op.successful:
            return op
        raise OperationFailed(op)
    last = op
    delay = interval
    consecutive_errors = 0
    while True:
        remaining = deadline - clock.monotonic()
        if remaining <= 0:
            raise OperationTimeout(op.id, last)
        clock.sleep(min(delay, remaining))
        try:
            last = get_operation(op.id)
        except ApiError as err:
            if not is_retriable(err):
                raise
            consecutive_errors += 1
            if max_poll_errors is not None and consecutive_errors > max_poll_errors:
                raise
            delay = error_backoff_fn(consecutive_errors)
            continue
        consecutive_errors = 0
        delay = interval
        if last.done:
            if last.successful:
                return last
            raise OperationFailed(last)


@dataclass
class FakeOperationServer:
    """Scripted server. `script` maps an operation id to a list of steps. A step is an
    Operation (returned) or an Exception (raised), consumed one per Get. The last step
    repeats. Create is idempotent on the idempotency key, like X-Idempotency-Key."""
    script: dict = field(default_factory=dict)
    creates: list = field(default_factory=list)
    gets: list = field(default_factory=list)
    _by_key: dict = field(default_factory=dict)

    def create(self, key, name, *, lose_response=False):
        if key in self._by_key:
            op = self._by_key[key]
        else:
            op = Operation(id=f"op-{len(self.creates) + 1}", resource_id=f"res-{name}")
            self.creates.append((key, name))
            self._by_key[key] = op
        if lose_response:
            raise ApiError("UNAVAILABLE", "response lost after the server accepted the request",
                           retry_type=RETRY_CALL)
        return op

    def get(self, op_id):
        self.gets.append(op_id)
        steps = self.script[op_id]
        step = steps.pop(0) if len(steps) > 1 else steps[0]
        if isinstance(step, Exception):
            raise step
        return step
