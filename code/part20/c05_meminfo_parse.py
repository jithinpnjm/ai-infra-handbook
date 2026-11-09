#!/usr/bin/env python3
"""Read /proc/meminfo the way an SRE should: available, cache, anonymous, locked.

'free' is not the number to alert on. MemAvailable is the kernel's estimate of memory
usable without swapping (Systems Performance 2nd ed, chapter 8, free).
Usage: python3 c05_meminfo_parse.py [/proc/meminfo]
"""
import sys


def parse_meminfo(text):
    """Return every line of meminfo as an integer in kB (counts such as HugePages stay plain)."""
    info = {}
    for line in text.strip().splitlines():
        key, _, rest = line.partition(":")
        info[key.strip()] = int(rest.split()[0])
    return info


def memory_view(info):
    """Split memory into the parts that matter for 'is this host in trouble'."""
    total = info["MemTotal"]
    cache = info.get("Buffers", 0) + info.get("Cached", 0)
    swap_used = info.get("SwapTotal", 0) - info.get("SwapFree", 0)
    return {
        "free_pct": 100.0 * info["MemFree"] / total,
        "available_pct": 100.0 * info["MemAvailable"] / total,
        "cache_kb": cache,
        "anon_kb": info.get("AnonPages", 0),
        "mlocked_kb": info.get("Mlocked", 0),
        "swap_used_kb": swap_used,
    }


def verdict(view, low_pct=10.0):
    """low_pct is a threshold you choose. The kernel does not define one."""
    if view["available_pct"] >= low_pct and view["swap_used_kb"] == 0:
        return "healthy: %.1f%% available (free is only %.1f%%, the rest is reclaimable cache)" % (
            view["available_pct"], view["free_pct"])
    if view["available_pct"] < low_pct:
        return "LOW available memory: %.1f%%; check PSI memory and the OOM log" % view[
            "available_pct"]
    return "available is fine but swap is in use: %d kB; check si/so in vmstat" % view[
        "swap_used_kb"]


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/proc/meminfo"
    with open(path) as handle:
        print(verdict(memory_view(parse_meminfo(handle.read()))))
