#!/usr/bin/env python3
"""Read cgroup cpu.stat and cpu.max and say whether a container is CPU throttled.

cgroup v2 cpu.stat keys: nr_periods, nr_throttled, throttled_usec (kernel docs).
cgroup v1 cpu.stat keys: nr_periods, nr_throttled, throttled_time in nanoseconds
(Systems Performance 2nd ed, chapter 11, Cgroup Statistics).
Usage: python3 c05_cpu_throttle.py BEFORE_FILE AFTER_FILE
"""
import sys


def parse_cpu_stat(text):
    """Return nr_periods, nr_throttled and throttled_usec as integers."""
    raw = {}
    for line in text.strip().splitlines():
        key, _, value = line.partition(" ")
        raw[key] = int(value)
    usec = raw.get("throttled_usec")
    if usec is None and "throttled_time" in raw:
        usec = raw["throttled_time"] // 1000
    if "nr_periods" not in raw or "nr_throttled" not in raw or usec is None:
        raise ValueError("cpu.stat has no throttling keys; is the cpu controller on?")
    return {"nr_periods": raw["nr_periods"], "nr_throttled": raw["nr_throttled"],
            "throttled_usec": usec}


def cpu_limit(text):
    """cpu.max is '$MAX $PERIOD' in microseconds. Return CPUs, or None for 'max'."""
    quota, period = text.split()
    return None if quota == "max" else int(quota) / int(period)


def burst_throttle_ms(limit_cpus, busy_threads, period_ms=100):
    """Milliseconds of each period spent throttled when all threads start at once.

    Production Kubernetes, chapter 12: 1 CPU limit, 5 busy threads, 100 ms period
    uses the 100 ms quota in 20 ms and is throttled for the other 80 ms.
    """
    quota_ms = limit_cpus * period_ms
    used_ms = quota_ms / busy_threads
    return max(0.0, period_ms - used_ms)


def report(before, after):
    """Throttle ratio and throttled seconds between two samples."""
    periods = after["nr_periods"] - before["nr_periods"]
    throttled = after["nr_throttled"] - before["nr_throttled"]
    usec = after["throttled_usec"] - before["throttled_usec"]
    ratio = throttled / periods if periods else 0.0
    return {"periods": periods, "throttled_periods": throttled,
            "throttle_ratio": ratio, "throttled_seconds": usec / 1e6}


if __name__ == "__main__":
    first = parse_cpu_stat(open(sys.argv[1]).read())
    second = parse_cpu_stat(open(sys.argv[2]).read())
    result = report(first, second)
    print(result)
    if result["throttled_periods"]:
        print("THROTTLED in %.0f%% of periods" % (100 * result["throttle_ratio"]))
    else:
        print("not throttled in this window")
