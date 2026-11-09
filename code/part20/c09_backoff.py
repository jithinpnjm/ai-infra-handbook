"""Retry with exponential backoff and jitter. Sleep and randomness are injected.

The herd simulation and the retry-budget maths live in c21_backoff_math.py (chapter 20.21).
"""
import random


def backoff_delay(attempt, base=0.1, cap=5.0, rng=random.random):
    """Full jitter: uniform between 0 and min(cap, base * 2**attempt). attempt starts at 0."""
    ceiling = min(cap, base * (2 ** attempt))
    return rng() * ceiling


class RetryableError(Exception):
    pass


def call_with_retry(fn, max_attempts=5, base=0.1, cap=5.0, deadline_s=None,
                    sleep=None, rng=random.random, clock=None):
    """Call fn(); retry RetryableError with full jitter. Other exceptions propagate at once.

    deadline_s bounds the total time. We never sleep past it.
    """
    import time
    sleep = sleep or time.sleep
    clock = clock or time.monotonic
    start = clock()
    for attempt in range(max_attempts):
        try:
            return fn()
        except RetryableError:
            if attempt == max_attempts - 1:
                raise
            delay = backoff_delay(attempt, base, cap, rng)
            if deadline_s is not None and clock() - start + delay >= deadline_s:
                raise
            sleep(delay)
