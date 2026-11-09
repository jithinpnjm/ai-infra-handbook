#!/usr/bin/env python3
"""Show the lookups a resolver tries for a name, given a resolv.conf.
Rule (resolv.conf(5)): a name with at least ndots dots is tried as written
first, then with each search domain. A name with fewer dots tries the search
domains first, then as written. A trailing dot means absolute: no search.
Each candidate costs two queries (A and AAAA) in a dual-stack pod."""
import sys

def parse_conf(text):
    search, ndots = [], 1
    for line in text.splitlines():
        f = line.split()
        if not f:
            continue
        if f[0] == "search":
            search = f[1:]
        elif f[0] == "options":
            for o in f[1:]:
                if o.startswith("ndots:"):
                    ndots = int(o.split(":")[1])
    return search, ndots

def candidates(name, search, ndots):
    if name.endswith("."):
        return [name]
    expanded = [f"{name}.{d}" for d in search]
    if name.count(".") >= ndots:
        return [name] + expanded
    return expanded + [name]

def queries_until_hit(name, conf, answers):
    """Count queries sent until a candidate in `answers` is found."""
    search, ndots = parse_conf(conf)
    sent = 0
    for c in candidates(name, search, ndots):
        sent += 2          # A + AAAA
        if c in answers:
            break
    return sent

if __name__ == "__main__":
    conf = sys.stdin.read()
    s, n = parse_conf(conf)
    for c in candidates(sys.argv[1], s, n):
        print(c)
