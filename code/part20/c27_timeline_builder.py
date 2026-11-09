#!/usr/bin/env python3
"""Turn timestamped incident notes into a timeline table and compute
time-to-detect, time-to-mitigate and time-to-resolve.

Note format, one per line:
    2026-03-14 09:12 UTC - Replica set 2 rolled out [started]
    2026-03-14 09:31 UTC - Pager fires on TTFT p99 [detected]
Optional tags: started, detected, mitigated, resolved. Lines starting with
# and blank lines are ignored. All times are measured from the "started" tag.

Usage: python3 c27_timeline_builder.py notes.txt
"""
import re
import sys
from datetime import datetime, timezone

TAGS = ("started", "detected", "mitigated", "resolved")
LINE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(?::\d{2})?\s*(?:Z|UTC)?\s*[-|]\s*"
    r"(.+?)(?:\s*\[(\w+)\])?\s*$"
)


class NoteError(ValueError):
    pass


def parse_notes(text):
    """Return a list of (datetime, text, tag-or-None) sorted by time."""
    events = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = LINE.match(line)
        if not m:
            raise NoteError(f"line {number}: cannot parse {line!r}")
        day, clock, what, tag = m.groups()
        if tag is not None:
            tag = tag.lower()
            if tag not in TAGS:
                raise NoteError(f"line {number}: unknown tag [{tag}]")
        when = datetime.strptime(f"{day} {clock}", "%Y-%m-%d %H:%M")
        events.append((when.replace(tzinfo=timezone.utc), what.strip(), tag))
    events.sort(key=lambda e: e[0])
    return events


def tag_times(events):
    """Map each tag to its first time. A repeated tag is an error."""
    found = {}
    for when, _what, tag in events:
        if tag is None:
            continue
        if tag in found:
            raise NoteError(f"tag [{tag}] used twice")
        found[tag] = when
    return found


def compute_metrics(events):
    """Return minutes for time_to_detect, time_to_mitigate, time_to_resolve.

    A metric is None when its tag is missing. Order must be
    started <= detected <= mitigated <= resolved.
    """
    found = tag_times(events)
    if "started" not in found:
        raise NoteError("no [started] tag: cannot measure from impact start")
    order = [t for t in TAGS if t in found]
    for a, b in zip(order, order[1:]):
        if found[b] < found[a]:
            raise NoteError(f"[{b}] happens before [{a}]")
    start = found["started"]

    def minutes(tag):
        return None if tag not in found else (found[tag] - start).total_seconds() / 60

    return {
        "time_to_detect": minutes("detected"),
        "time_to_mitigate": minutes("mitigated"),
        "time_to_resolve": minutes("resolved"),
    }


def format_minutes(value):
    if value is None:
        return "not recorded"
    return f"{value:g} min"


def build_timeline(text):
    """Return the markdown timeline section for the given notes."""
    events = parse_notes(text)
    metrics = compute_metrics(events)
    lines = ["## Timeline", "", "| Time (UTC) | Event | Marker |", "|---|---|---|"]
    for when, what, tag in events:
        lines.append(f"| {when:%Y-%m-%d %H:%M} | {what} | {tag or ''} |")
    lines += [
        "",
        f"- Time to detect: {format_minutes(metrics['time_to_detect'])}",
        f"- Time to mitigate: {format_minutes(metrics['time_to_mitigate'])}",
        f"- Time to resolve: {format_minutes(metrics['time_to_resolve'])}",
        "",
    ]
    return "\n".join(lines)


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as handle:
            print(build_timeline(handle.read()))
    except (OSError, NoteError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
