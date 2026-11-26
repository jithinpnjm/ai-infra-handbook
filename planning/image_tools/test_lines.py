def check_line(text, box_width, font_size=24, is_mono=False, name=""):
    factor = 0.62 if is_mono else 0.60
    char_w = factor * font_size
    text_w = len(text) * char_w
    pad_left = 16
    pad_right = box_width - text_w - pad_left
    ok = (text_w <= box_width - 32)
    print(f"[{'OK' if ok else 'FAIL'}] {name:15s} len={len(text):2d} w={text_w:5.1f}px box={box_width}px right_pad={pad_right:5.1f}px | '{text}'")
    return ok

print("--- Testing Col 1 (w=220, sans 24) ---")
# 'Parquet or JSON Lines'
check_line("Parquet or", 220, 24, False, "Col1 row6")
check_line("JSON Lines", 220, 24, False, "Col1 row6")

print("\n--- Testing Col 2 (w=240, sans 24) ---")
# 'machine interchange'
check_line("machine", 240, 24, False)
check_line("interchange", 240, 24, False)
# 'configs people edit by hand'
check_line("configs people", 240, 24, False)
check_line("edit by hand", 240, 24, False)
# 'tool settings'
check_line("tool settings", 240, 24, False)
# 'tabular exports'
check_line("tabular exports", 240, 24, False)
# 'legacy config'
check_line("legacy config", 240, 24, False)
# 'large datasets'
check_line("large datasets", 240, 24, False)

print("\n--- Testing Col 3 (w=530, mono 24) ---")
# json safe call: 'json.loads, json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str)'
check_line("json.loads,", 530, 24, True)
check_line("json.dumps(data, indent=2,", 530, 24, True)
check_line("sort_keys=True,", 530, 24, True)
check_line("ensure_ascii=False, default=str)", 530, 24, True)

# yaml safe call: 'yaml.safe_load, yaml.safe_dump(sort_keys=False), yaml.safe_load_all for multi-document manifests; ruamel.yaml preserves comments'
check_line("yaml.safe_load,", 530, 24, True)
check_line("yaml.safe_dump(sort_keys=False),", 530, 24, True)
check_line("yaml.safe_load_all for", 530, 24, True)
check_line("multi-document manifests;", 530, 24, True)
check_line("ruamel.yaml preserves comments", 530, 24, True)

# toml safe call: 'tomllib.loads (read-only stdlib since 3.11; tomli-w to write)'
check_line("tomllib.loads (read-only", 530, 24, True)
check_line("stdlib since 3.11;", 530, 24, True)
check_line("tomli-w to write)", 530, 24, True)

# csv safe call: 'csv.DictReader and DictWriter with newline="" and encoding'
check_line("csv.DictReader and DictWriter", 530, 24, True)
check_line('with newline="" and encoding', 530, 24, True)

# ini safe call: 'configparser: cp[db].getint(port, fallback=5432)'
check_line("configparser:", 530, 24, True)
check_line("cp[db].getint(port, fallback=5432)", 530, 24, True)

# parquet safe call: '-'
check_line("-", 530, 24, True)

print("\n--- Testing Col 4 (w=530, sans/mono 24) ---")
# json trap: 'float precision, large integers, NaN, duplicate keys; JSON Lines for streaming: for line in open(events.jsonl): json.loads(line)'
check_line("float precision, large integers,", 530, 24, False)
check_line("NaN, duplicate keys; JSON Lines", 530, 24, False)
check_line("for streaming: for line in", 530, 24, False)
check_line("open(events.jsonl):", 530, 24, True)
check_line("json.loads(line)", 530, 24, True)

# yaml trap: 'never yaml.load on untrusted input (arbitrary object construction); the Norway problem: region: no becomes boolean False'
check_line("never yaml.load on untrusted input", 530, 24, False)
check_line("(arbitrary object construction);", 530, 24, False)
check_line("the Norway problem: region: no", 530, 24, False)
check_line("becomes boolean False", 530, 24, False)

# toml trap: 'no stdlib writer'
check_line("no stdlib writer", 530, 24, False)

# csv trap: 'spreadsheets may use utf-8-sig or cp1252; large data: pandas (chapter 3.10)'
check_line("spreadsheets may use utf-8-sig", 530, 24, False)
check_line("or cp1252; large data: pandas", 530, 24, False)
check_line("(chapter 3.10)", 530, 24, False)

# ini trap: '-'
check_line("-", 530, 24, False)

# parquet trap: '-'
check_line("-", 530, 24, False)
