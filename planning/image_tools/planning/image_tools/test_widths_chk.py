#!/usr/bin/env python3
import sys

def calc_width(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * fs * factor

print("=== CHECKING TEXT WIDTHS FOR COL WIDTH 740 ===")
box_w = 740
# usable width with 20px padding on each side inside an inner card:
card_w = 700 # 20px padding from outer box
card_usable = 660 # 20px padding inside card

texts = [
    ("which value is used", 30, False),
    ("type", 30, False),
    ("render template", 30, False),
    ("condition", 30, False),
    ("ansible-inventory --host", 24, True),
    ("debug var", 24, True),
    ("-vvv", 24, True),
    ("grep", 24, True),
    ("extra vars with -e sit at the top of the stack and role vars/ also beats inventory", 24, False),
    ("var | type_debug shows str, int, bool, list, dict", 24, False),
    ("ansible localhost -m template with -e @vars.yml", 24, True),
    ("inspect /tmp/out", 24, True),
    ("debug msg of the when expression", 24, False),
    ("-vv false_condition", 24, True),
    ("gpu_count 8 from -e is a number, from a CSV it is the text 8 and the when comparison fails", 24, False),
]

for t, fs, is_mono in texts:
    w = calc_width(t, fs, is_mono)
    print(f"[{'MONO' if is_mono else 'SANS'}] fs={fs} len={len(t):2d} w={w:6.1f} px : '{t}'")
