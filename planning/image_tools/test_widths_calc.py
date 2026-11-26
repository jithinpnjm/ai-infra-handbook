#!/usr/bin/env python3
import sys

def text_width(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * factor * fs

def check_card(card_name, lines, card_width, padding=16, fs=24, is_mono=False):
    max_avail = card_width - 2 * padding
    print(f"\n--- {card_name} (width={card_width}, avail={max_avail:.1f}) ---")
    all_ok = True
    for l in lines:
        w = text_width(l, fs, is_mono)
        status = "OK" if w <= max_avail else "OVERFLOW"
        if w > max_avail:
            all_ok = False
        print(f"  [{status}] len={len(l):2d} w={w:5.1f} / {max_avail:.1f} | '{l}'")
    return all_ok

items = [
    ("Title Line 1", ["Sizing the tail sampler and what "], 1520, 16, 48, False),
    ("Title Line 2", ["happens at 8,000 traces per second"], 1520, 16, 48, False),
    ("Formula", ["traces held = new traces per second x decision_wait"], 1520, 16, 30, False),
    ("Design point header", ["Design point"], 740, 16, 30, False),
    ("Left Item 1", [
        "5,000 new traces per second x 30 s ",
        "= 150,000 traces held"
    ], 700, 16, 24, False),
    ("Left Item 2", ["num_traces set to 200,000 gives headroom"], 700, 16, 24, False),
    ("Left Item 3", [
        "with 20 spans of 1 KB each (assumptions, ",
        "not measurements) = 3 GB of buffered span ",
        "data before overhead"
    ], 700, 16, 24, False),
    ("Right Header", ["After a traffic increase"], 740, 16, 30, False),
    ("Right Item", [
        "8,000 per second x 30 s = 240,000 needed, ",
        "which exceeds num_traces 200,000, so ",
        "traces are dropped and the viewer ",
        "shows fragments"
    ], 700, 16, 24, False),
    ("Fix 1", ["raise num_traces and memory together"], 700, 16, 24, False),
    ("Fix 2", ["or reduce decision_wait"], 700, 16, 24, False),
    ("Fix 3", ["add sampler replicas"], 700, 16, 24, False),
    ("Fix 4", [
        "apply a head sample in tier one ",
        "to cut the rate"
    ], 700, 16, 24, False),
    ("Fix 5", ["alert on refusals"], 700, 16, 24, False),
    ("Check 1", [
        "otelcol_receiver_refused_spans non-zero ",
        "means the memory limiter is shedding load"
    ], 700, 16, 24, False),
    ("Check 2", [
        "if the load balancing tier was scaled up, ",
        "spans of one trace may be split across ",
        "samplers while the routing pool changes"
    ], 700, 16, 24, False)
]

all_passed = True
for name, lines, cw, pad, fs, mono in items:
    ok = check_card(name, lines, cw, pad, fs, mono)
    if not ok:
        all_passed = False

print(f"\nAll lines fit within conservative limits? {all_passed}")
