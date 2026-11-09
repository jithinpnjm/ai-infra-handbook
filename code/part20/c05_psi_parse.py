#!/usr/bin/env python3
"""Parse Linux pressure stall information (PSI) text and give a plain verdict.

Format (kernel docs, accounting/psi): a line per kind, 'some' and optionally 'full',
    some avg10=0.00 avg60=0.00 avg300=0.00 total=0
avg values are percent of time stalled over 10, 60 and 300 seconds.
total is cumulative stall time in microseconds.
Usage: python3 c05_psi_parse.py /proc/pressure/cpu
"""
import sys


def parse_psi(text):
    """Return {'some': {...}, 'full': {...}}. Each value is a dict of floats."""
    out = {}
    for line in text.strip().splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[0] not in ("some", "full"):
            raise ValueError("not a PSI line: %r" % line)
        fields = {}
        for item in parts[1:]:
            key, _, value = item.partition("=")
            fields[key] = float(value)
        out[parts[0]] = fields
    if "some" not in out:
        raise ValueError("no 'some' line found")
    return out


def trend(entry, margin=1.0):
    """Compare the 10 second average with the 300 second average."""
    delta = entry["avg10"] - entry["avg300"]
    if delta > margin:
        return "rising"
    if delta < -margin:
        return "falling"
    return "steady"


def verdict(psi, warn=10.0):
    """One sentence for a human. warn is a percent chosen by you, not by the kernel."""
    some = psi["some"]
    word = trend(some)
    if some["avg10"] < warn and some["avg60"] < warn:
        return "no meaningful stall (some avg10=%.2f), trend %s" % (some["avg10"], word)
    full = psi.get("full")
    if full and full["avg10"] >= warn:
        return "ALL non-idle tasks stalled %.2f%% of 10s, trend %s" % (full["avg10"], word)
    return "some tasks stalled %.2f%% of 10s, trend %s" % (some["avg10"], word)


if __name__ == "__main__":
    for path in sys.argv[1:]:
        with open(path) as handle:
            print(path, "->", verdict(parse_psi(handle.read())))
