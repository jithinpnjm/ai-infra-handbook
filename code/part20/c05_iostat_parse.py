#!/usr/bin/env python3
"""Parse 'iostat -x' / 'iostat -sxz' device rows and flag what deserves a look.

Columns are read from the header line, so the short (-s) and wide layouts both work.
Column meanings: Systems Performance 2nd ed, chapter 9, iostat. await is the average
response time in ms including OS queueing. %util is busy time only and says little
about devices that serve many requests in parallel.
Usage: iostat -sxz 1 5 | python3 c05_iostat_parse.py
"""
import sys


def parse_iostat(text):
    """Return a list of dicts, one per device row, using the latest 'Device' header."""
    rows, header = [], None
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0].startswith("Device"):
            header = parts
        elif header and len(parts) == len(header):
            try:
                values = [float(x) for x in parts[1:]]
            except ValueError:
                continue
            rows.append(dict(zip(header[1:], values), device=parts[0]))
    return rows


def notes(row, await_ms=10.0, util_pct=60.0):
    """Thresholds are the book's rule of thumb: over 60 percent busy, await over about 10 ms."""
    out = []
    wait = row.get("await", max(row.get("r_await", 0.0), row.get("w_await", 0.0)))
    util = row.get("%util", 0.0)
    if wait > await_ms:
        out.append("slow: await %.2f ms" % wait)
    if util >= util_pct and wait <= await_ms:
        out.append("busy but fast: judge by IOPS and MB/s, not %util")
    size = row.get("areq-sz", row.get("wareq-sz"))
    if size is not None and size <= 8:
        out.append("small requests (%.1f kB): random access present" % size)
    if row.get("rqm/s", 0) > 0:
        out.append("merging requests: some sequential access")
    return out or ["no flag"]


if __name__ == "__main__":
    for row in parse_iostat(sys.stdin.read()):
        print(row["device"], "; ".join(notes(row)))
