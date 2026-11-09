#!/usr/bin/env python3
"""Judge conntrack table pressure from sysctl-style text.
Input lines look like: net.netfilter.nf_conntrack_count = 31000
Exit code 2 when usage is at or above the alert fraction."""
import re, sys

def read_values(text):
    vals = {}
    for m in re.finditer(r"nf_conntrack_(count|max)\s*=\s*(\d+)", text):
        vals[m.group(1)] = int(m.group(2))
    return vals

def usage(text):
    v = read_values(text)
    if "count" not in v or "max" not in v or v["max"] == 0:
        raise ValueError("need nf_conntrack_count and nf_conntrack_max")
    return v["count"] / v["max"]

def verdict(frac, alert=0.8):
    if frac >= 1.0:
        return "FULL: no space left, new connections cannot be made"
    if frac >= alert:
        return "HOT: raise nf_conntrack_max or cut short-lived flows"
    return "ok"

if __name__ == "__main__":
    f = usage(sys.stdin.read())
    print(f"{f:.1%} {verdict(f)}")
    sys.exit(2 if f >= 0.8 else 0)
