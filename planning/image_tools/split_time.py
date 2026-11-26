text = "datetime.now(timezone.utc) for aware datetimes; time.monotonic() for durations, immune to clock changes; time.time() wall clock; time.perf_counter() for benchmarks; zoneinfo.ZoneInfo(Europe/Berlin) for time zones; datetime.fromisoformat and ISO 8601 with a timezone; store UTC and log in UTC; avoid naive datetimes"

# Let's break by semicolons or phrases:
parts = text.split("; ")
print("Parts count:", len(parts))
for p in parts:
    print(f"  '{p}' (len={len(p)})")
