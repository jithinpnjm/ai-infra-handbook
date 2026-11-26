#!/usr/bin/env python3

def check_wrap(name, lines, max_w, fs=24, is_mono=False):
    coeff = 0.62 if is_mono else 0.60
    print(f"\n--- Checking {name} (box_w={max_w}, fs={fs}, {'mono' if is_mono else 'sans'}) ---")
    all_ok = True
    for i, line in enumerate(lines, 1):
        w = len(line) * fs * coeff
        pad = (max_w - w) / 2
        ok = pad >= 16.0
        print(f"  Line {i}: '{line}' | w={w:.1f}px, pad={pad:.1f}px [{'OK' if ok else 'FAIL'}]")
        if not ok: all_ok = False
    return all_ok

check_wrap("Event 1", ["spec edit"], 300, fs=26)
check_wrap("Event 2", ["label edit"], 300, fs=26)
check_wrap("Event 3", ["status write", "by controller"], 300, fs=24)
check_wrap("Event 4", ["controller", "finishes reconcile"], 300, fs=24)
