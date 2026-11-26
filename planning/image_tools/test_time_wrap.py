def test_wrap():
    w_avail = 1520 - 70 # icon and padding
    
    # Time panel text:
    time_lines = [
        "datetime.now(timezone.utc) for aware datetimes; time.monotonic() for durations, immune to clock changes;",
        "time.time() wall clock; time.perf_counter() for benchmarks; zoneinfo.ZoneInfo(Europe/Berlin) for time zones;",
        "datetime.fromisoformat and ISO 8601 with a timezone; store UTC and log in UTC; avoid naive datetimes"
    ]
    for i, ln in enumerate(time_lines):
        w = len(ln) * 24 * 0.60
        print(f"Time line {i+1}: len={len(ln)}, w={w:.1f}px (avail {w_avail}px, margin {w_avail - w:.1f}px)")
        
    # If 4 lines for time panel:
    time_lines_4 = [
        "datetime.now(timezone.utc) for aware datetimes; time.monotonic() for durations, immune to clock changes;",
        "time.time() wall clock; time.perf_counter() for benchmarks;",
        "zoneinfo.ZoneInfo(Europe/Berlin) for time zones; datetime.fromisoformat and ISO 8601 with a timezone;",
        "store UTC and log in UTC; avoid naive datetimes"
    ]
    print("\n--- 4 lines ---")
    for i, ln in enumerate(time_lines_4):
        w = len(ln) * 24 * 0.60
        print(f"Time line {i+1}: len={len(ln)}, w={w:.1f}px (avail {w_avail}px, margin {w_avail - w:.1f}px)")

test_wrap()
