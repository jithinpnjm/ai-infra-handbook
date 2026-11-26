import re

prompt_spec = """Title: Data format cheat sheet: purpose, safe call and trap

CONTENT (use exactly these labels, each once, spelled exactly; add nothing else):
A table with columns 'Format', 'Use for', 'Safe call', 'Trap'. 'JSON' / 'machine interchange' / 'json.loads, json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str)' / 'float precision, large integers, NaN, duplicate keys; JSON Lines for streaming: for line in open(events.jsonl): json.loads(line)'. 'YAML' / 'configs people edit by hand' / 'yaml.safe_load, yaml.safe_dump(sort_keys=False), yaml.safe_load_all for multi-document manifests; ruamel.yaml preserves comments' / 'never yaml.load on untrusted input (arbitrary object construction); the Norway problem: region: no becomes boolean False' (orange). 'TOML' / 'tool settings' / 'tomllib.loads (read-only stdlib since 3.11; tomli-w to write)' / 'no stdlib writer'. 'CSV' / 'tabular exports' / 'csv.DictReader and DictWriter with newline="" and encoding' / 'spreadsheets may use utf-8-sig or cp1252; large data: pandas (chapter 3.10)'. 'INI' / 'legacy config' / 'configparser: cp[db].getint(port, fallback=5432)' / '-'. 'Parquet or JSON Lines' / 'large datasets' / '-' / '-'. Rules strip 'validate parsed data with a schema or pydantic; handle JSONDecodeError and YAMLError with file and line context; never eval data'. Time panel 'datetime.now(timezone.utc) for aware datetimes; time.monotonic() for durations, immune to clock changes; time.time() wall clock; time.perf_counter() for benchmarks; zoneinfo.ZoneInfo(Europe/Berlin) for time zones; datetime.fromisoformat and ISO 8601 with a timezone; store UTC and log in UTC; avoid naive datetimes'. Story strip 'a metrics export contains NaN that the next tool in the chain refuses to read'. Bottom bar: 'Choose each format for its purpose, and parse with the safe call'.
"""

# Extract title
title_m = re.search(r"Title:\s*(.+)", prompt_spec)
title = title_m.group(1).strip() if title_m else ""
print("Title:", title)

# Extract quoted strings
quoted = re.findall(r"'([^']*)'", prompt_spec)
print(f"Total quoted items: {len(quoted)}")
for i, q in enumerate(quoted, 1):
    print(f"{i:2d}. '{q}'")
