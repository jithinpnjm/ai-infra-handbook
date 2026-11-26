# Let's test the 4 lines for time panel
time_lines = [
    "datetime.now(timezone.utc) for aware datetimes; time.monotonic() for durations,",
    "immune to clock changes; time.time() wall clock; time.perf_counter() for benchmarks;",
    "zoneinfo.ZoneInfo(Europe/Berlin) for time zones; datetime.fromisoformat and",
    "ISO 8601 with a timezone; store UTC and log in UTC; avoid naive datetimes"
]

full_time = " ".join(time_lines)
orig_time = "datetime.now(timezone.utc) for aware datetimes; time.monotonic() for durations, immune to clock changes; time.time() wall clock; time.perf_counter() for benchmarks; zoneinfo.ZoneInfo(Europe/Berlin) for time zones; datetime.fromisoformat and ISO 8601 with a timezone; store UTC and log in UTC; avoid naive datetimes"

print("Equal?:", full_time == orig_time)
assert full_time == orig_time

for i, ln in enumerate(time_lines, 1):
    w = len(ln) * 24 * 0.60
    print(f"Line {i}: len={len(ln)}, w={w:.1f}px (right pad in 1520-110={1410}px: {1410-w:.1f}px)")
