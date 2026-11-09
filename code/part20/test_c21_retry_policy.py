from datetime import datetime, timezone

from c21_retry_policy import (Attempt, decide, parse_retry_after,
                              remaining_deadline, check_timeouts)

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_retry_after_seconds_and_date():
    assert parse_retry_after("120") == 120.0
    assert parse_retry_after("Thu, 01 Jan 2026 12:02:00 GMT", NOW) == 120.0
    assert parse_retry_after("Wed, 31 Dec 2025 12:00:00 GMT", NOW) == 0.0
    assert parse_retry_after("soon") is None and parse_retry_after(None) is None


def test_never_replay_after_first_token():
    d = decide(Attempt(status=503, first_token_sent=True))
    assert d.action == "fail" and "stream" in d.reason


def test_503_goes_to_another_replica_and_honours_retry_after():
    d = decide(Attempt(status=503, retry_after="2"))
    assert d.action == "retry_other_replica" and d.delay_s == 2.0


def test_429_waits_and_does_not_hop_replicas():
    d = decide(Attempt(status=429, retry_after="7"))
    assert d.action == "retry_later" and d.delay_s == 7.0
    assert decide(Attempt(status=429)).action == "fail"


def test_budget_and_attempt_limit_stop_retries():
    assert decide(Attempt(status=503, budget_ok=False)).action == "fail"
    assert decide(Attempt(status=503, attempts_made=2, max_attempts=2)).action == "fail"


def test_client_errors_never_retry():
    for s in (400, 401, 403, 404, 413, 422):
        assert decide(Attempt(status=s)).action == "fail"


def test_side_effects_need_a_key_unless_request_never_arrived():
    assert decide(Attempt(status=503, side_effects=True)).action == "fail"
    assert decide(Attempt(status=503, side_effects=True, idempotency_key=True)).action != "fail"
    assert decide(Attempt(error="connect_failure", side_effects=True)).action == "retry_other_replica"


def test_timeout_before_first_token_retries_once():
    assert decide(Attempt(error="timeout")).action == "retry_other_replica"
    assert decide(Attempt(status=500)).action == "retry_other_replica"
    assert decide(Attempt(status=500, attempts_made=2, max_attempts=3)).action == "fail"


def test_deadline_propagation_matches_sre_book_example():
    assert remaining_deadline(30, 7, margin_s=0) == 23
    assert remaining_deadline(1, 5) == 0.0


def test_timeout_chain_good_and_bad():
    assert check_timeouts(60, 40, 18, 2, 15, max_backoff_s=1) == []
    bad = check_timeouts(30, 40, 18, 3, 20)
    assert len(bad) == 3
