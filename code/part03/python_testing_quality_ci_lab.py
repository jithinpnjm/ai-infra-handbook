#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.9: Testing, quality and CI for Python tooling."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_testing_quality_ci import (
    Drainer,
    FakeKube,
    FakeTestinfraHost,
    run_five_iteration_alternatives,
    timer_bestof,
    timer_bestoftotal,
    timer_once,
    timer_total,
    verify_sshd_host,
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
    # 1. LP Ch. 21 timer2.py (once, total, bestof, bestoftotal) & 5 iteration alternatives
    t_once, r_once = timer_once(pow, 2, 10)
    t_tot, r_tot = timer_total(str.upper, "hack", _reps=50)
    t_best, r_best = timer_bestof(str.upper, "hack", _reps=5)
    t_bt, r_bt = timer_bestoftotal(str.upper, "hack", _reps1=3, _reps=20)
    alts = run_five_iteration_alternatives(100)
    check(
        "LP Ch. 21 timer functions return (elapsed, result) and all 5 iteration alternatives produce identical results",
        r_once == 1024
        and r_tot == "HACK"
        and r_best == "HACK"
        and r_bt == "HACK"
        and t_once >= 0.0
        and t_tot >= t_best >= 0.0
        and alts["forLoop"] == alts["listComp"] == alts["mapCall"] == alts["genExpr"] == alts["genFunc"],
    )

    # 2. Section 3 Drainer with injected clock and sleep (success and timeout paths without real sleeping)
    ticks = iter(range(0, 100, 5))
    fk_ok = FakeKube([["pod-a", "pod-b"], ["pod-b"], []])
    drainer_ok = Drainer(fk_ok, clock=lambda: float(next(ticks)), sleep=lambda s: None)
    polls = drainer_ok.drain("gpu-node-01", timeout=30.0)

    ticks_to = iter(range(0, 100, 10))
    fk_to = FakeKube([["stuck-pod"]] * 10)
    drainer_to = Drainer(fk_to, clock=lambda: float(next(ticks_to)), sleep=lambda s: None)
    timed_out = False
    try:
        drainer_to.drain("gpu-node-02", timeout=15.0)
    except TimeoutError:
        timed_out = True
    check(
        "Drainer cordons node, drains in 2 polls when pods evacuate, and raises TimeoutError deterministically when stuck",
        fk_ok.cordoned == ["gpu-node-01"] and polls == 2 and timed_out is True,
    )

    # 3. AUR Ch. 14 Testinfra SSH host verification assertions
    host = FakeTestinfraHost()
    check(
        "Testinfra verifier asserts openssh-server package, sshd service, 0644 ed25519 host key, and sshd user",
        verify_sshd_host(host) is True,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
