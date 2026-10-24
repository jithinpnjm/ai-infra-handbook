#!/usr/bin/env python3
"""Plan a Slurm upgrade path from the documented compatibility window.

Rule (Upgrade Guide): each major release accepts upgrades from the previous N majors (N=2 before 24.11,
N=3 from 24.11 on). Releases YY.MM: 23.02, 23.11, 24.05, 24.11, 25.05, 25.11, 26.05, 26.11, 27.05 ...
Usage: slurm_upgrade_path.py CURRENT TARGET  (e.g. 22.05 26.05)
"""
import sys

# 9-month cycle until 24.05, then 6-month cycle (from the guide's "Release Cycle" section).
RELEASES = ["20.02", "20.11", "21.08", "22.05", "23.02", "23.11", "24.05", "24.11", "25.05", "25.11", "26.05", "26.11", "27.05"]


def window(target):
    i = RELEASES.index(target)
    n = 3 if RELEASES.index(target) >= RELEASES.index("24.11") else 2
    return RELEASES[max(0, i - n):i]


def path(cur, tgt):
    steps, here = [], cur
    while here != tgt:
        reachable = [r for r in RELEASES if RELEASES.index(r) > RELEASES.index(here) and here in window(r)]
        nxt = [r for r in reachable if RELEASES.index(r) <= RELEASES.index(tgt)]
        if not nxt:
            raise SystemExit(f"no path from {here} to {tgt}")
        here = nxt[-1]          # the furthest compatible step not past the target
        steps.append(here)
    return steps


if __name__ == "__main__":
    cur, tgt = sys.argv[1], sys.argv[2]
    s = path(cur, tgt)
    print(f"{cur} -> " + " -> ".join(s) + f"   ({len(s)} upgrade step{'s' if len(s) != 1 else ''})")
    for r in s:
        print(f"  {r} accepts upgrades from: {', '.join(window(r))}")
