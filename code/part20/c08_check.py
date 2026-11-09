# code/part20/c08_check.py
"""A tiny testing harness for the coding round (chapter 20.8).

Paste the part you need into a plain editor. It uses only the standard library.
"""
import copy
import math
import random
import time


def _same(got, want, unordered, tol):
    if unordered:
        try:
            got, want = sorted(got), sorted(want)
        except TypeError:
            pass
    if tol is not None and isinstance(got, float) and isinstance(want, float):
        return math.isclose(got, want, rel_tol=tol, abs_tol=tol)
    return got == want


def check(fn, cases, unordered=False, tol=None, verbose=True):
    """Run fn on (args, expected) pairs. Return the list of failures.

    Each call gets a deep copy of args, so a function that changes its
    input cannot hide a bug in the next case. An exception counts as a failure.
    """
    failures = []
    for i, (args, want) in enumerate(cases):
        if not isinstance(args, tuple):
            args = (args,)
        start = time.perf_counter()
        try:
            got = fn(*copy.deepcopy(args))
        except Exception as exc:  # report, do not stop
            got = "raised %s: %s" % (type(exc).__name__, exc)
            ok = False
        else:
            ok = _same(got, want, unordered, tol)
        ms = (time.perf_counter() - start) * 1000
        if verbose:
            print("%-4s case %d args=%r got=%r want=%r (%.2f ms)"
                  % ("ok" if ok else "FAIL", i, args, got, want, ms))
        if not ok:
            failures.append((i, args, got, want))
    if verbose:
        print("%d of %d passed" % (len(cases) - len(failures), len(cases)))
    return failures


def stress(fast, brute, make_input, runs=300, seed=0):
    """Compare a fast solution with a slow obvious one on random small input.

    Returns the first input where they differ, or None.
    """
    rng = random.Random(seed)
    for _ in range(runs):
        args = make_input(rng)
        if fast(*copy.deepcopy(args)) != brute(*copy.deepcopy(args)):
            return args
    return None
