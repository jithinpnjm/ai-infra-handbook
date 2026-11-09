"""Log parsing and aggregation with hash maps."""
from collections import Counter, defaultdict


def parse_line(line):
    """Parse 'ts method path status latency_ms'. Return a dict or None if malformed."""
    parts = line.split()
    if len(parts) != 5:
        return None
    ts, method, path, status, ms = parts
    try:
        return {"ts": int(ts), "method": method, "path": path,
                "status": int(status), "ms": float(ms)}
    except ValueError:
        return None


def aggregate(lines):
    """One pass. Return (stats per path, number of malformed lines)."""
    stats = defaultdict(lambda: {"n": 0, "errors": 0, "ms_total": 0.0})
    bad = 0
    for line in lines:
        rec = parse_line(line)
        if rec is None:
            bad += 1
            continue
        s = stats[rec["path"]]
        s["n"] += 1
        s["errors"] += rec["status"] >= 500
        s["ms_total"] += rec["ms"]
    return dict(stats), bad


def error_rate(stat):
    return stat["errors"] / stat["n"] if stat["n"] else 0.0


def top_paths(lines, k):
    """The k most frequent paths, ties broken by path name so output is stable."""
    counts = Counter(rec["path"] for rec in map(parse_line, lines) if rec)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]


def first_duplicate_request_id(ids):
    """Return the first id that was already seen, else None. O(n) with a set."""
    seen = set()
    for i in ids:
        if i in seen:
            return i
        seen.add(i)
    return None
