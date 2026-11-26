#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

def generate_svg():
    # Grid coordinates
    x1, w1 = 40, 186
    gap = 8
    x2, w2 = x1 + w1 + gap, 242   # 234, 242 -> 476
    x3, w3 = x2 + w2 + gap, 530   # 484, 530 -> 1014
    x4, w4 = x3 + w3 + gap, 538   # 1022, 538 -> 1560

    # Vertical coordinates
    # Title at y=56
    hy = 74
    hh = 56
    # Let's check row heights:
    # Row 1 (JSON, 5 lines, dy=23): H_text = 4*23 + 24 = 116. h = 116 + 34 = 150.
    # Row 2 (YAML, 5 lines, dy=23): H_text = 116. h = 150.
    # Row 3 (TOML, 2 lines, dy=25): H_text = 25 + 24 = 49. h = 49 + 33 = 82.
    # Row 4 (CSV, 3 lines, dy=25): H_text = 50 + 24 = 74. h = 74 + 34 = 108.
    # Row 5 (INI, 3 lines, dy=25): H_text = 74. h = 108.
    # Row 6 (Parquet, 2 lines, dy=25): H_text = 49. h = 82.

    # Story strip: 1 line fs=24 -> h = 24 + 32 = 56.
    # Rules strip: 2 lines fs=24, dy=25 -> h = 49 + 33 = 82.
    # Time panel: 4 lines fs=24, dy=25 -> h = 75 + 24 + 33 = 132.
    # Bottom bar: 1 line fs=26 -> h = 26 + 32 = 58.

    # Let's compute total height:
    gap_r = 6
    cur_y = hy + hh + gap_r
    
    rows = []
    # (id, h)
    r_heights = [148, 148, 80, 106, 106, 80]
    
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    lines.append('  <title>Data format cheat sheet: purpose, safe call and trap</title>')
    lines.append('  <desc>A cheat sheet table comparing data formats JSON, YAML, TOML, CSV, INI, and Parquet with their purpose, safe calls, and traps, plus time functions, validation rules, and error story.</desc>')
    lines.append('  <!-- Canvas Background -->')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    lines.append('  <!-- Title -->')
    lines.append('  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Data format cheat sheet: purpose, safe call and trap</text>')

    # Column Headers
    lines.append(f'  <!-- Column Headers -->')
    lines.append(f'  <rect x="{x1}" y="{hy}" width="{w1}" height="{hh}" rx="8" fill="#207448"/>')
    lines.append(f'  <text x="{x1 + w1/2}" y="{hy + 38}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Format</text>')

    lines.append(f'  <rect x="{x2}" y="{hy}" width="{w2}" height="{hh}" rx="8" fill="#207448"/>')
    lines.append(f'  <text x="{x2 + w2/2}" y="{hy + 38}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Use for</text>')

    lines.append(f'  <rect x="{x3}" y="{hy}" width="{w3}" height="{hh}" rx="8" fill="#207448"/>')
    lines.append(f'  <text x="{x3 + w3/2}" y="{hy + 38}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Safe call</text>')

    lines.append(f'  <rect x="{x4}" y="{hy}" width="{w4}" height="{hh}" rx="8" fill="#207448"/>')
    lines.append(f'  <text x="{x4 + w4/2}" y="{hy + 38}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Trap</text>')

    # Row 1: JSON
    ry1, rh1 = cur_y, 148
    lines.append(f'  <!-- Row 1: JSON -->')
    lines.append(f'  <rect x="{x1}" y="{ry1}" width="{w1}" height="{rh1}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Icon for JSON: braces { }
    lines.append(f'  <g transform="translate({x1 + 18}, {ry1 + 48})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 12 4 C 6 4 4 8 4 16 C 4 22 1 24 1 24 C 1 24 4 26 4 32 C 4 40 6 44 12 44"/>')
    lines.append('    <path d="M 26 4 C 32 4 34 8 34 16 C 34 22 37 24 37 24 C 37 24 34 26 34 32 C 34 40 32 44 26 44"/>')
    lines.append('  </g>')
    lines.append(f'  <text x="{x1 + 120}" y="{ry1 + 83}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">JSON</text>')

    lines.append(f'  <rect x="{x2}" y="{ry1}" width="{w2}" height="{rh1}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x2 + w2/2}" y="{ry1 + 67}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x2 + w2/2}" dy="0">machine</tspan>')
    lines.append(f'    <tspan x="{x2 + w2/2}" dy="27">interchange</tspan>')
    lines.append('  </text>')

    lines.append(f'  <rect x="{x3}" y="{ry1}" width="{w3}" height="{rh1}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x3 + 24}" y="{ry1 + 35}" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x3 + 24}" dy="0">json.loads,</tspan>')
    lines.append(f'    <tspan x="{x3 + 24}" dy="26">json.dumps(data, indent=2,</tspan>')
    lines.append(f'    <tspan x="{x3 + 24}" dy="26">sort_keys=True,</tspan>')
    lines.append(f'    <tspan x="{x3 + 24}" dy="26">ensure_ascii=False, default=str)</tspan>')
    lines.append('  </text>')

    lines.append(f'  <rect x="{x4}" y="{ry1}" width="{w4}" height="{rh1}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x4 + 22}" y="{ry1 + 33}" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x4 + 22}" dy="0">float precision, large integers,</tspan>')
    lines.append(f'    <tspan x="{x4 + 22}" dy="23">NaN, duplicate keys;</tspan>')
    lines.append(f'    <tspan x="{x4 + 22}" dy="23">JSON Lines for streaming:</tspan>')
    lines.append(f'    <tspan x="{x4 + 22}" dy="23" font-family="monospace">for line in open(events.jsonl):</tspan>')
    lines.append(f'    <tspan x="{x4 + 22}" dy="23" font-family="monospace">json.loads(line)</tspan>')
    lines.append('  </text>')

    cur_y += rh1 + gap_r

    # Row 2: YAML
    ry2, rh2 = cur_y, 148
    lines.append(f'  <!-- Row 2: YAML -->')
    lines.append(f'  <rect x="{x1}" y="{ry2}" width="{w1}" height="{rh2}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Icon for YAML: document
    lines.append(f'  <g transform="translate({x1 + 18}, {ry2 + 48})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="4" y="4" width="32" height="42" rx="4"/>')
    lines.append('    <line x1="10" y1="14" x2="24" y2="14"/>')
    lines.append('    <line x1="10" y1="23" x2="28" y2="23"/>')
    lines.append('    <line x1="10" y1="32" x2="24" y2="32"/>')
    lines.append('  </g>')
    lines.append(f'  <text x="{x1 + 120}" y="{ry2 + 83}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">YAML</text>')

    lines.append(f'  <rect x="{x2}" y="{ry2}" width="{w2}" height="{rh2}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x2 + w2/2}" y="{ry2 + 67}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x2 + w2/2}" dy="0">configs people</tspan>')
    lines.append(f'    <tspan x="{x2 + w2/2}" dy="27">edit by hand</tspan>')
    lines.append('  </text>')

    lines.append(f'  <rect x="{x3}" y="{ry2}" width="{w3}" height="{rh2}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x3 + 22}" y="{ry2 + 33}" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x3 + 22}" dy="0" font-family="monospace">yaml.safe_load,</tspan>')
    lines.append(f'    <tspan x="{x3 + 22}" dy="23" font-family="monospace">yaml.safe_dump(sort_keys=False),</tspan>')
    lines.append(f'    <tspan x="{x3 + 22}" dy="23">yaml.safe_load_all for</tspan>')
    lines.append(f'    <tspan x="{x3 + 22}" dy="23">multi-document manifests;</tspan>')
    lines.append(f'    <tspan x="{x3 + 22}" dy="23">ruamel.yaml preserves comments</tspan>')
    lines.append('  </text>')

    # Orange YAML trap
    lines.append(f'  <rect x="{x4}" y="{ry2}" width="{w4}" height="{rh2}" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="2.5"/>')
    lines.append(f'  <rect x="{x4}" y="{ry2}" width="8" height="{rh2}" rx="3" fill="#db8129"/>')
    lines.append(f'  <text x="{x4 + 24}" y="{ry2 + 33}" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x4 + 24}" dy="0">never yaml.load on</tspan>')
    lines.append(f'    <tspan x="{x4 + 24}" dy="23">untrusted input</tspan>')
    lines.append(f'    <tspan x="{x4 + 24}" dy="23">(arbitrary object construction);</tspan>')
    lines.append(f'    <tspan x="{x4 + 24}" dy="23">the Norway problem: region: no</tspan>')
    lines.append(f'    <tspan x="{x4 + 24}" dy="23">becomes boolean False</tspan>')
    lines.append('  </text>')

    cur_y += rh2 + gap_r

    # Row 3: TOML
    ry3, rh3 = cur_y, 80
    lines.append(f'  <!-- Row 3: TOML -->')
    lines.append(f'  <rect x="{x1}" y="{ry3}" width="{w1}" height="{rh3}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Icon for TOML: tool/wrench
    lines.append(f'  <g transform="translate({x1 + 18}, {ry3 + 18})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <circle cx="15" cy="15" r="9"/>')
    lines.append('    <line x1="22" y1="22" x2="34" y2="34" stroke-width="4"/>')
    lines.append('  </g>')
    lines.append(f'  <text x="{x1 + 120}" y="{ry3 + 49}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">TOML</text>')

    lines.append(f'  <rect x="{x2}" y="{ry3}" width="{w2}" height="{rh3}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x2 + w2/2}" y="{ry3 + 49}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">tool settings</text>')

    lines.append(f'  <rect x="{x3}" y="{ry3}" width="{w3}" height="{rh3}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x3 + 24}" y="{ry3 + 35}" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x3 + 24}" dy="0" font-family="monospace">tomllib.loads (read-only stdlib</tspan>')
    lines.append(f'    <tspan x="{x3 + 24}" dy="26">since 3.11; tomli-w to write)</tspan>')
    lines.append('  </text>')

    lines.append(f'  <rect x="{x4}" y="{ry3}" width="{w4}" height="{rh3}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x4 + 24}" y="{ry3 + 49}" font-family="sans-serif" font-size="24" fill="#303a36">no stdlib writer</text>')

    cur_y += rh3 + gap_r

    # Row 4: CSV
    ry4, rh4 = cur_y, 106
    lines.append(f'  <!-- Row 4: CSV -->')
    lines.append(f'  <rect x="{x1}" y="{ry4}" width="{w1}" height="{rh4}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Icon for CSV: grid/table
    lines.append(f'  <g transform="translate({x1 + 18}, {ry4 + 30})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="4" y="4" width="34" height="34" rx="4"/>')
    lines.append('    <line x1="4" y1="18" x2="38" y2="18"/>')
    lines.append('    <line x1="19" y1="4" x2="19" y2="38"/>')
    lines.append('  </g>')
    lines.append(f'  <text x="{x1 + 120}" y="{ry4 + 62}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">CSV</text>')

    lines.append(f'  <rect x="{x2}" y="{ry4}" width="{w2}" height="{rh4}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x2 + w2/2}" y="{ry4 + 46}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x2 + w2/2}" dy="0">tabular</tspan>')
    lines.append(f'    <tspan x="{x2 + w2/2}" dy="27">exports</tspan>')
    lines.append('  </text>')

    lines.append(f'  <rect x="{x3}" y="{ry4}" width="{w3}" height="{rh4}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x3 + 24}" y="{ry4 + 46}" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x3 + 24}" dy="0" font-family="monospace">csv.DictReader and DictWriter</tspan>')
    lines.append(f'    <tspan x="{x3 + 24}" dy="27">with newline="" and encoding</tspan>')
    lines.append('  </text>')

    lines.append(f'  <rect x="{x4}" y="{ry4}" width="{w4}" height="{rh4}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x4 + 24}" y="{ry4 + 34}" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x4 + 24}" dy="0">spreadsheets may use utf-8-sig</tspan>')
    lines.append(f'    <tspan x="{x4 + 24}" dy="26">or cp1252; large data: pandas</tspan>')
    lines.append(f'    <tspan x="{x4 + 24}" dy="26">(chapter 3.10)</tspan>')
    lines.append('  </text>')

    cur_y += rh4 + gap_r

    # Row 5: INI
    ry5, rh5 = cur_y, 106
    lines.append(f'  <!-- Row 5: INI -->')
    lines.append(f'  <rect x="{x1}" y="{ry5}" width="{w1}" height="{rh5}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Icon for INI: settings sliders
    lines.append(f'  <g transform="translate({x1 + 18}, {ry5 + 30})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="4" y="4" width="34" height="34" rx="4"/>')
    lines.append('    <circle cx="21" cy="21" r="6"/>')
    lines.append('  </g>')
    lines.append(f'  <text x="{x1 + 120}" y="{ry5 + 62}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">INI</text>')

    lines.append(f'  <rect x="{x2}" y="{ry5}" width="{w2}" height="{rh5}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x2 + w2/2}" y="{ry5 + 62}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">legacy config</text>')

    lines.append(f'  <rect x="{x3}" y="{ry5}" width="{w3}" height="{rh5}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x3 + 24}" y="{ry5 + 34}" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="{x3 + 24}" dy="0">configparser:</tspan>')
    lines.append(f'    <tspan x="{x3 + 24}" dy="26">cp[db].getint(port,</tspan>')
    lines.append(f'    <tspan x="{x3 + 24}" dy="26">fallback=5432)</tspan>')
    lines.append('  </text>')

    lines.append(f'  <rect x="{x4}" y="{ry5}" width="{w4}" height="{rh5}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x4 + w4/2}" y="{ry5 + 62}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">-</text>')

    cur_y += rh5 + gap_r

    # Row 6: Parquet or JSON Lines
    ry6, rh6 = cur_y, 80
    lines.append(f'  <!-- Row 6: Parquet or JSON Lines -->')
    lines.append(f'  <rect x="{x1}" y="{ry6}" width="{w1}" height="{rh6}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    lines.append(f'  <text x="{x1 + w1/2}" y="{ry6 + 34}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    lines.append(f'    <tspan x="{x1 + w1/2}" dy="0">Parquet or</tspan>')
    lines.append(f'    <tspan x="{x1 + w1/2}" dy="26">JSON Lines</tspan>')
    lines.append('  </text>')

    lines.append(f'  <rect x="{x2}" y="{ry6}" width="{w2}" height="{rh6}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x2 + w2/2}" y="{ry6 + 48}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">large datasets</text>')

    lines.append(f'  <rect x="{x3}" y="{ry6}" width="{w3}" height="{rh6}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x3 + w3/2}" y="{ry6 + 48}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">-</text>')

    lines.append(f'  <rect x="{x4}" y="{ry6}" width="{w4}" height="{rh6}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    lines.append(f'  <text x="{x4 + w4/2}" y="{ry6 + 48}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">-</text>')

    cur_y += rh6 + 10

    # Story Strip: 'a metrics export contains NaN that the next tool in the chain refuses to read'
    story_y, story_h = cur_y, 56
    lines.append(f'  <!-- Story Strip -->')
    lines.append(f'  <rect x="40" y="{story_y}" width="1520" height="{story_h}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    # Icon for story strip
    lines.append(f'  <g transform="translate(56, {story_y + 11})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 6 4 L 24 4 L 32 12 L 32 32 L 6 32 Z"/>')
    lines.append('    <line x1="12" y1="16" x2="20" y2="16"/>')
    lines.append('    <line x1="12" y1="22" x2="26" y2="22"/>')
    lines.append('  </g>')
    lines.append(f'  <text x="108" y="{story_y + 36}" font-family="sans-serif" font-size="24" fill="#303a36">a metrics export contains NaN that the next tool in the chain refuses to read</text>')

    cur_y += story_h + 8

    # Rules Strip: 'validate parsed data with a schema or pydantic; handle JSONDecodeError and YAMLError with file and line context; never eval data'
    rules_y, rules_h = cur_y, 80
    lines.append(f'  <!-- Rules Strip -->')
    lines.append(f'  <rect x="40" y="{rules_y}" width="1520" height="{rules_h}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.8"/>')
    # Icon for rules strip: shield/check
    lines.append(f'  <g transform="translate(56, {rules_y + 18})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 6 8 L 18 2 L 30 8 L 30 20 C 30 28 18 36 18 36 C 18 36 6 28 6 20 Z"/>')
    lines.append('    <polyline points="12,18 16,22 24,14"/>')
    lines.append('  </g>')
    lines.append(f'  <text x="108" y="{rules_y + 33}" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="108" dy="0">validate parsed data with a schema or pydantic; handle JSONDecodeError and YAMLError</tspan>')
    lines.append(f'    <tspan x="108" dy="27">with file and line context; never eval data</tspan>')
    lines.append('  </text>')

    cur_y += rules_h + 8

    # Time Panel
    time_y, time_h = cur_y, 134
    lines.append(f'  <!-- Time Panel -->')
    lines.append(f'  <rect x="40" y="{time_y}" width="1520" height="{time_h}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Clock icon
    lines.append(f'  <g transform="translate(56, {time_y + 42})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <circle cx="24" cy="24" r="20"/>')
    lines.append('    <polyline points="24,12 24,24 33,24"/>')
    lines.append('  </g>')
    lines.append(f'  <text x="116" y="{time_y + 34}" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append(f'    <tspan x="116" dy="0">datetime.now(timezone.utc) for aware datetimes; time.monotonic() for durations,</tspan>')
    lines.append(f'    <tspan x="116" dy="25">immune to clock changes; time.time() wall clock; time.perf_counter() for benchmarks;</tspan>')
    lines.append(f'    <tspan x="116" dy="25">zoneinfo.ZoneInfo(Europe/Berlin) for time zones; datetime.fromisoformat and</tspan>')
    lines.append(f'    <tspan x="116" dy="25">ISO 8601 with a timezone; store UTC and log in UTC; avoid naive datetimes</tspan>')
    lines.append('  </text>')

    cur_y += time_h + 8

    # Bottom Bar: 'Choose each format for its purpose, and parse with the safe call'
    bot_y, bot_h = cur_y, 54
    lines.append(f'  <!-- Bottom Bar -->')
    lines.append(f'  <rect x="40" y="{bot_y}" width="1520" height="{bot_h}" rx="8" fill="#207448"/>')
    lines.append(f'  <text x="800" y="{bot_y + 36}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Choose each format for its purpose, and parse with the safe call</text>')

    lines.append('</svg>')

    return "\n".join(lines), bot_y + bot_h

svg_text, final_h = generate_svg()
print(f"Final total height used: {final_h}px")
with open("final_candidate.svg", "w") as f:
    f.write(svg_text)
