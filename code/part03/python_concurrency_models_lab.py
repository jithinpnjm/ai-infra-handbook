#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.6: Concurrency: threads, processes and asyncio."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_concurrency_models import (
    bounded_map,
    is_prime,
    run_async_semaphore_and_comprehension_demo,
    run_async_spinner_cancellation_demo,
    run_thread_spinner_demo,
    run_threadpool_to_do_map,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. FP Ch. 19 is_prime & spinner_thread.py (threading.Event) & spinner_async.py (Task.cancel)
    _, thread_stopped = run_thread_spinner_demo()
    ans, async_cancelled = asyncio.run(run_async_spinner_cancellation_demo())
    check(
        "is_prime identifies primes/composites, threading.Event stops spinner thread, and Task.cancel() raises CancelledError",
        is_prime(2) is True
        and is_prime(3333333333333333) is False
        and is_prime(299593572317531) is True
        and thread_stopped is True
        and ans == 42
        and async_cancelled is True,
    )

    # 2. FP Ch. 20 flags2_threadpool.py pattern (to_do_map + as_completed + per-future error isolation)
    res, errs = run_threadpool_to_do_map([2, 9, 13, 17], fail_on=9)
    check(
        "to_do_map + as_completed collects prime results {2: True, 13: True, 17: True} and isolates error on 9",
        res == {2: True, 13: True, 17: True} and errs == {9: "ValueError"},
    )

    # 3. Section 2 bounded_map backpressure helper
    b_res = sorted(bounded_map(lambda x: x * 3, range(25), workers=3, max_inflight=5))
    check(
        "bounded_map processes all 25 items with max_inflight=5 backpressure",
        b_res == [x * 3 for x in range(25)],
    )

    # 4. FP Ch. 21 & LP Ch. 20: asyncio.Semaphore, to_thread, multi_probe async generator, and AsyncRange
    async_out = asyncio.run(run_async_semaphore_and_comprehension_demo())
    check(
        "asyncio.Semaphore(2) caps max_active<=2, to_thread doubles 0..5, and PEP 530 async comprehensions collect results",
        async_out["gathered"] == [0, 2, 4, 6, 8, 10]
        and 1 <= async_out["max_active"] <= 2
        and async_out["found_dict"] == {"python.org": True, "rust-lang.org": True, "invalid.local": False}
        and async_out["async_range_vals"] == [1, 4, 9, 16],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
