"""Retry decisions for a streaming completions API, plus a timeout nesting check.

The rules are one reasonable design, not a Nebius design. They follow HTTP
semantics (RFC 9110 sections 9.2.2, 10.2.3, 15.6.4) and the guidance in the
Google SRE book chapters on overload and cascading failures.
Standard library only.
"""
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Optional

NEVER_RETRY_STATUS = {400, 401, 403, 404, 413, 422}


@dataclass(frozen=True)
class Attempt:
    status: Optional[int] = None        # HTTP status, None if no response came
    error: Optional[str] = None         # "connect_failure" or "timeout" or None
    first_token_sent: bool = False      # did the client already receive output?
    side_effects: bool = False          # does the call change server state?
    idempotency_key: bool = False       # did the client send a key?
    retry_after: Optional[str] = None   # raw Retry-After header value
    attempts_made: int = 1
    max_attempts: int = 2
    budget_ok: bool = True              # retry budget has a token


@dataclass(frozen=True)
class Decision:
    action: str                         # retry_other_replica | retry_later | fail
    reason: str
    delay_s: float = 0.0


def parse_retry_after(value, now=None):
    """Return seconds to wait, or None. Accepts delay-seconds or an HTTP-date."""
    if value is None:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return max(0.0, (when - now).total_seconds())


def decide(a: Attempt, now=None) -> Decision:
    if a.first_token_sent:
        return Decision("fail", "output already started: surface the broken stream, never replay")
    if a.side_effects and not a.idempotency_key and a.error != "connect_failure":
        return Decision("fail", "call has side effects and no idempotency key")
    if a.attempts_made >= a.max_attempts:
        return Decision("fail", "attempt limit reached")
    if a.status in NEVER_RETRY_STATUS:
        return Decision("fail", "client error: a retry returns the same answer")
    if a.status == 429:
        wait = parse_retry_after(a.retry_after, now)
        if wait is None:
            return Decision("fail", "429 without Retry-After: let the client back off")
        return Decision("retry_later", "tenant over limit: another replica does not help", wait)
    if not a.budget_ok:
        return Decision("fail", "retry budget is empty")
    if a.error == "connect_failure":
        return Decision("retry_other_replica", "request never reached a server")
    if a.status == 503:
        return Decision("retry_other_replica", "overloaded or draining replica",
                        parse_retry_after(a.retry_after, now) or 0.0)
    if a.error == "timeout" or a.status == 504:
        return Decision("retry_other_replica", "no first token in time; cancel the first copy")
    if a.status == 500 and a.attempts_made == 1:
        return Decision("retry_other_replica", "one retry for a request-level engine error")
    return Decision("fail", "not a retryable failure")


def remaining_deadline(deadline_s, elapsed_s, margin_s=0.2):
    """Deadline to hand to the next hop: what is left, minus a small margin."""
    return max(0.0, deadline_s - elapsed_s - margin_s)


def check_timeouts(client_s, gateway_total_s, gateway_per_try_s, gateway_attempts,
                   engine_s, max_backoff_s=0.0, margin_s=0.2):
    """Return a list of problems with a client > gateway > engine timeout chain."""
    problems = []
    if engine_s >= gateway_per_try_s:
        problems.append("engine timeout must be shorter than the gateway per-try timeout")
    worst = (gateway_per_try_s * gateway_attempts
             + max_backoff_s * max(0, gateway_attempts - 1))
    if worst > gateway_total_s:
        problems.append(f"{gateway_attempts} tries need up to {worst:g}s "
                        f"but the gateway total is {gateway_total_s:g}s")
    if gateway_total_s + margin_s > client_s:
        problems.append("client gives up before the gateway can answer")
    return problems
