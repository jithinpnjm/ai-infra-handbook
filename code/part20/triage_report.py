#!/usr/bin/env python3
"""Print USE-style findings for a directory written by first60.sh.

Usage: python3 triage_report.py DIR
Reads nproc.txt, uptime.txt, vmstat.txt, free.txt, iostat.txt and mpstat.txt.
A missing file is reported as a known-unknown, not as an error.
"""
import os
import sys

import triage_findings as f
import triage_parse as p


def read(d, name):
    path = os.path.join(d, name)
    return open(path).read() if os.path.exists(path) else None


def report(d):
    out = []
    cpus = int(read(d, "nproc.txt").split()[0])
    jobs = [
        ("uptime.txt", lambda t: f.load_findings(p.parse_uptime(t), cpus)),
        ("vmstat.txt", lambda t: f.vmstat_findings(p.parse_vmstat(t), cpus)),
        ("free.txt", lambda t: f.free_findings(p.parse_free(t))),
        ("iostat.txt", lambda t: f.iostat_findings(p.parse_iostat(t))),
        ("mpstat.txt", lambda t: f.mpstat_findings(p.parse_mpstat(t))),
    ]
    for name, fn in jobs:
        text = read(d, name)
        if text is None:
            out.append(f.Finding("known-unknown", "E", f"{name} missing"))
            continue
        if text.startswith("missing tool"):
            out.append(f.Finding("known-unknown", "E", f"{name} not readable: {text.strip()}"))
            continue
        try:
            out.extend(fn(text))
        except (ValueError, KeyError):
            first = text.strip().splitlines()[0] if text.strip() else "empty"
            out.append(f.Finding("known-unknown", "E", f"{name} not readable: {first}"))
    dm = read(d, "dmesg.txt")
    if dm is not None and "exit " in dm and " from: dmesg" in dm:
        out.append(f.Finding("known-unknown", "E", "dmesg.txt not readable: " + dm.strip().splitlines()[0]))
    elif dm and p.find_oom(dm):
        out.append(f.Finding("memory", "E", f"dmesg mentions {len(p.find_oom(dm))} OOM or killed lines"))
    order = {"E": 0, "S": 1, "U": 2}
    return sorted(out, key=lambda x: order[x.kind])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    for item in report(sys.argv[1]):
        print(f"{item.kind}  {item.resource:<14} {item.message}")
