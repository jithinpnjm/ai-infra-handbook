#!/usr/bin/env python3
"""Will an inference pod fit its HOST memory limit? Plain arithmetic from stated inputs.

Every input is yours. Nothing here is a measured default. The reasoning it encodes:
- Anonymous memory and pinned (page-locked) memory cannot be reclaimed. They count
  against the cgroup limit and the OOM killer acts when they alone reach it.
- Page cache from reading weight files also counts against the cgroup limit,
  but it can be reclaimed first (kernel docs: memory.stat file versus anon).
Usage: python3 c05_host_mem_budget.py LIMIT_GIB WORKERS PINNED_GIB ANON_GIB CACHE_GIB
"""
import sys

GIB = 2 ** 30


def weights_gib(params, bytes_per_param):
    """Size of the weights in GiB: parameters times bytes per parameter."""
    return params * bytes_per_param / GIB


def budget(limit_gib, workers, pinned_gib, anon_gib, cache_gib):
    """pinned_gib and anon_gib are per worker process. cache_gib is shared."""
    unreclaimable = workers * (pinned_gib + anon_gib)
    worst_case = unreclaimable + cache_gib
    return {
        "unreclaimable_gib": unreclaimable,
        "with_cache_gib": worst_case,
        "headroom_gib": limit_gib - unreclaimable,
        "fits": unreclaimable < limit_gib,
        "cache_pressure": worst_case > limit_gib,
    }


def explain(result):
    if not result["fits"]:
        return "OOM kill expected: %.1f GiB cannot be reclaimed, limit is lower" % result[
            "unreclaimable_gib"]
    if result["cache_pressure"]:
        return "fits, but page cache will be reclaimed constantly (slow weight reloads)"
    return "fits with %.1f GiB headroom" % result["headroom_gib"]


if __name__ == "__main__":
    lim, workers, pinned, anon, cache = (float(x) for x in sys.argv[1:6])
    print(explain(budget(lim, int(workers), pinned, anon, cache)))
