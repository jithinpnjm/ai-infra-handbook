"""Parse a Statuspage incidents.json and estimate per-component availability.

Input shape: the Atlassian Statuspage API v2 /incidents.json, as served by
status.nebius.com. The API returns only the most recent 50 incidents, so the
window starts at the oldest incident returned. Everything computed here is an
estimate from public status posts, not a measurement.

Run: python3 c37_status_history.py c37_status_incidents_fixture.json
"""
from __future__ import annotations

import json
import statistics
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

IMPACT_ORDER = {"none": 0, "minor": 1, "major": 2, "critical": 3}


class StatusDataError(ValueError):
    """The incident data is malformed or internally inconsistent."""


def parse_ts(text: str) -> datetime:
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (AttributeError, ValueError) as exc:
        raise StatusDataError(f"bad timestamp: {text!r}") from exc


@dataclass
class Incident:
    id: str
    name: str
    impact: str
    start: datetime
    end: datetime | None  # None means still open
    first_update: datetime
    targets: list = field(default_factory=list)  # list of (region, service)
    has_postmortem: bool = False


def split_component(label: str):
    """'EU-NORTH1 - Compute Cloud' -> ('EU-NORTH1', 'Compute Cloud')."""
    if " - " in label:
        region, service = label.split(" - ", 1)
        return region.strip(), service.strip()
    return "UNKNOWN", label.strip()


def load_incidents(data) -> list:
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, dict) or "incidents" not in data:
        raise StatusDataError("missing 'incidents' list")
    out = []
    for raw in data["incidents"]:
        for key in ("id", "name", "impact", "created_at"):
            if key not in raw:
                raise StatusDataError(f"incident missing {key!r}")
        if raw["impact"] not in IMPACT_ORDER:
            raise StatusDataError(f"unknown impact {raw['impact']!r}")
        start = parse_ts(raw["created_at"])
        end = parse_ts(raw["resolved_at"]) if raw.get("resolved_at") else None
        if end is not None and end < start:
            raise StatusDataError(f"{raw['id']}: resolved before created")
        updates = raw.get("incident_updates", [])
        stamps = [parse_ts(u["created_at"]) for u in updates] or [start]
        targets = set()
        for u in updates:
            for a in u.get("affected_components") or []:
                targets.add(split_component(a["name"]))
        if not targets:
            for c in raw.get("components") or []:
                targets.add(("UNKNOWN", c["name"]))
        if not targets:
            targets.add(("UNKNOWN", "unattributed"))
        out.append(Incident(
            id=raw["id"], name=raw["name"], impact=raw["impact"], start=start,
            end=end, first_update=min(stamps), targets=sorted(targets),
            has_postmortem=any(u.get("status") == "postmortem" for u in updates)))
    return out


def merge_intervals(intervals):
    """Union of (start, end) pairs so overlapping incidents count once."""
    merged = []
    for s, e in sorted(intervals):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def window_of(incidents, as_of):
    if not incidents:
        raise StatusDataError("no incidents, window undefined")
    start = min(i.start for i in incidents)
    if as_of <= start:
        raise StatusDataError("as_of is not after the oldest incident")
    return start, as_of


def component_report(incidents, as_of, min_impact="major", by="service"):
    """Per component: incident count, minutes down, availability, median repair.

    A component is counted as fully down for the whole incident, so the
    availability is a pessimistic lower bound for partial outages.
    """
    floor = IMPACT_ORDER[min_impact]
    w_start, w_end = window_of(incidents, as_of)
    window_min = (w_end - w_start).total_seconds() / 60
    buckets: dict = {}
    for inc in incidents:
        if IMPACT_ORDER[inc.impact] < floor:
            continue
        end = min(inc.end or as_of, as_of)
        keys = {(t[1] if by == "service" else t) for t in inc.targets}
        for key in keys:
            buckets.setdefault(key, []).append((inc, inc.start, end))
    rows = []
    for key, items in buckets.items():
        down = sum((e - s).total_seconds() / 60 for s, e in
                   merge_intervals([(s, e) for _, s, e in items]))
        repairs = [(e - s).total_seconds() / 60 for _, s, e in items]
        rows.append({
            "component": key, "incidents": len(items),
            "down_minutes": round(down, 1),
            "availability": round(100 * (1 - down / window_min), 3),
            "median_minutes": round(statistics.median(repairs), 1),
            "longest_minutes": round(max(repairs), 1)})
    rows.sort(key=lambda r: -r["down_minutes"])
    return {"window_start": w_start.isoformat(), "window_minutes": round(window_min),
            "min_impact": min_impact, "rows": rows}


def public_ack_lag_minutes(inc: Incident):
    """Minutes from incident start to the first public update."""
    return (inc.first_update - inc.start).total_seconds() / 60


def main(argv):
    path = argv[1]
    with open(path) as fh:
        raw = json.load(fh)
    as_of = parse_ts(raw.get("_fixture", {}).get("fetched", "2026-11-11") + "T00:00:00Z")
    incs = load_incidents(raw)
    for level in ("major", "minor"):
        rep = component_report(incs, as_of, min_impact=level)
        print(f"\nwindow {rep['window_start'][:10]} + {rep['window_minutes']} min, impact >= {level}")
        for r in rep["rows"][:8]:
            print(f"{r['component']:38} n={r['incidents']:2} down={r['down_minutes']:7} "
                  f"avail={r['availability']}% median={r['median_minutes']}m")


if __name__ == "__main__":
    main(sys.argv)
