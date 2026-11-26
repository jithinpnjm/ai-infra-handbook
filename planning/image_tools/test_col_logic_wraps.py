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

check_wrap("Col 2 Logic (3 lines)", [
    "generation increments",
    "only when",
    "spec changes"
], 345)

check_wrap("Col 3 Logic (4 lines)", [
    "observedGeneration is",
    "written by the controller",
    "to record the generation",
    "it last reconciled"
], 415)
